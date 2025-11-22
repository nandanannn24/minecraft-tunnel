from flask import Flask, request, jsonify
import socket
import threading
import time
from threading import Lock
import logging

app = Flask(__name__)

# Konfigurasi
MINECRAFT_SERVER_HOST = '192.168.1.4'  # Ganti dengan IP komputer kamu
MINECRAFT_SERVER_PORT = 25565
TUNNEL_PORT = 25565  # Port yang akan digunakan di Railway

class MinecraftTunnel:
    def __init__(self):
        self.connections = {}
        self.lock = Lock()
        
    def handle_client(self, client_socket, client_address):
        try:
            # Connect ke server Minecraft lokal
            minecraft_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            minecraft_socket.connect((MINECRAFT_SERVER_HOST, MINECRAFT_SERVER_PORT))
            
            # Simpan connection
            with self.lock:
                self.connections[client_address] = {
                    'client': client_socket,
                    'minecraft': minecraft_socket
                }
            
            # Forward data bidirectional
            def forward_to_minecraft():
                try:
                    while True:
                        data = client_socket.recv(4096)
                        if not data:
                            break
                        minecraft_socket.sendall(data)
                except:
                    pass
            
            def forward_to_client():
                try:
                    while True:
                        data = minecraft_socket.recv(4096)
                        if not data:
                            break
                        client_socket.sendall(data)
                except:
                    pass
            
            # Jalankan thread untuk forwarding
            thread1 = threading.Thread(target=forward_to_minecraft)
            thread2 = threading.Thread(target=forward_to_client)
            
            thread1.start()
            thread2.start()
            
            thread1.join()
            thread2.join()
            
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            # Cleanup
            with self.lock:
                if client_address in self.connections:
                    del self.connections[client_address]
            client_socket.close()
            try:
                minecraft_socket.close()
            except:
                pass

    def start_tunnel_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind(('0.0.0.0', TUNNEL_PORT))
            server_socket.listen(5)
            print(f"Tunnel server listening on port {TUNNEL_PORT}")
            
            while True:
                client_socket, client_address = server_socket.accept()
                print(f"New connection from {client_address}")
                
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            server_socket.close()

# Jalankan tunnel server
tunnel = MinecraftTunnel()

@app.route('/')
def home():
    return jsonify({
        "status": "Minecraft Tunnel Server is running",
        "minecraft_server": f"{MINECRAFT_SERVER_HOST}:{MINECRAFT_SERVER_PORT}",
        "tunnel_port": TUNNEL_PORT
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def start_tunnel():
    time.sleep(2)  # Tunggu Flask start
    tunnel.start_tunnel_server()

if __name__ == "__main__":
    # Jalankan tunnel server di thread terpisah
    tunnel_thread = threading.Thread(target=start_tunnel)
    tunnel_thread.daemon = True
    tunnel_thread.start()
    
    # Jalankan Flask app
    app.run(host='0.0.0.0', port=8080, debug=False)