import os
from flask import Flask, jsonify
import socket
import threading
import time
import logging

app = Flask(__name__)

# FORCE port 25565 untuk Minecraft tunnel
MINECRAFT_SERVER_HOST = os.environ.get('MINECRAFT_HOST', 'localhost')
MINECRAFT_SERVER_PORT = int(os.environ.get('MINECRAFT_PORT', '25565'))
TUNNEL_PORT = 25565  # ← FORCE 25565, jangan pakai environment variable

# Web dashboard port
WEB_PORT = 8080

class MinecraftTunnel:
    def __init__(self):
        self.connections = {}
        self.lock = threading.Lock()
        
    def handle_client(self, client_socket, client_address):
        try:
            print(f"🔄 New Minecraft connection from {client_address}")
            
            # Connect ke Minecraft server lokal via client
            minecraft_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            minecraft_socket.settimeout(30)
            minecraft_socket.connect((MINECRAFT_SERVER_HOST, MINECRAFT_SERVER_PORT))
            
            print(f"✅ Tunnel established for {client_address}")
            
            # Forward data bidirectional
            def forward_to_minecraft():
                try:
                    while True:
                        data = client_socket.recv(4096)
                        if not data:
                            break
                        minecraft_socket.sendall(data)
                except Exception as e:
                    print(f"❌ Error forwarding to minecraft: {e}")
            
            def forward_to_client():
                try:
                    while True:
                        data = minecraft_socket.recv(4096)
                        if not data:
                            break
                        client_socket.sendall(data)
                except Exception as e:
                    print(f"❌ Error forwarding to client: {e}")
            
            thread1 = threading.Thread(target=forward_to_minecraft)
            thread2 = threading.Thread(target=forward_to_client)
            
            thread1.daemon = True
            thread2.daemon = True
            
            thread1.start()
            thread2.start()
            
            thread1.join()
            thread2.join()
            
        except Exception as e:
            print(f"❌ Error handling client {client_address}: {e}")
        finally:
            with self.lock:
                if client_address in self.connections:
                    del self.connections[client_address]
            try:
                client_socket.close()
            except:
                pass
            try:
                minecraft_socket.close()
            except:
                pass

    def start_tunnel_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind(('0.0.0.0', TUNNEL_PORT))
            server_socket.listen(10)
            print(f"🚀 Minecraft Tunnel Server started on port {TUNNEL_PORT}")
            print(f"🎯 Forwarding to: {MINECRAFT_SERVER_HOST}:{MINECRAFT_SERVER_PORT}")
            
            while True:
                try:
                    client_socket, client_address = server_socket.accept()
                    
                    with self.lock:
                        self.connections[client_address] = {
                            'client': client_socket,
                            'minecraft': None
                        }
                    
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    print(f"❌ Accept error: {e}")
                
        except Exception as e:
            print(f"❌ Tunnel server error: {e}")
        finally:
            server_socket.close()

# Jalankan tunnel server
tunnel = MinecraftTunnel()

@app.route('/')
def home():
    return jsonify({
        "status": "Minecraft Tunnel Server is running",
        "minecraft_server": f"{MINECRAFT_SERVER_HOST}:{MINECRAFT_SERVER_PORT}",
        "tunnel_port": TUNNEL_PORT,
        "web_port": WEB_PORT,
        "active_connections": len(tunnel.connections)
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "connections": len(tunnel.connections)})

def start_tunnel():
    time.sleep(3)  # Beri waktu untuk web server start
    print("🔄 Starting Minecraft tunnel...")
    tunnel.start_tunnel_server()

if __name__ == "__main__":
    print("🎮 Starting Minecraft Tunnel Server...")
    
    # Jalankan tunnel di thread terpisah
    tunnel_thread = threading.Thread(target=start_tunnel)
    tunnel_thread.daemon = True
    tunnel_thread.start()
    
    # Jalankan web dashboard di port 8080
    print(f"🌐 Web dashboard running on port {WEB_PORT}")
    app.run(host='0.0.0.0', port=WEB_PORT, debug=False, threaded=True)
