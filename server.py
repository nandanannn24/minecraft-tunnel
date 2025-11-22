import os
from flask import Flask
import socket
import threading
import time

app = Flask(__name__)

# Gunakan environment variables dari Railway
MINECRAFT_SERVER_HOST = os.environ.get('MINECRAFT_HOST', 'localhost')
MINECRAFT_SERVER_PORT = int(os.environ.get('MINECRAFT_PORT', '25565'))
TUNNEL_PORT = int(os.environ.get('PORT', '25565'))

class MinecraftTunnel:
    def __init__(self):
        self.connections = {}
        self.lock = threading.Lock()
        
    def handle_client(self, client_socket, client_address):
        try:
            print(f"New connection from {client_address}")
            
            # Connect ke Minecraft server via client tunnel
            minecraft_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            minecraft_socket.settimeout(30)
            minecraft_socket.connect((MINECRAFT_SERVER_HOST, MINECRAFT_SERVER_PORT))
            print(f"Connected to Minecraft server at {MINECRAFT_SERVER_HOST}:{MINECRAFT_SERVER_PORT}")
            
            # Forward data
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
            
            t1 = threading.Thread(target=forward_to_minecraft)
            t2 = threading.Thread(target=forward_to_client)
            t1.daemon = True
            t2.daemon = True
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
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
            server_socket.listen(10)
            print(f"Minecraft Tunnel Server started on port {TUNNEL_PORT}")
            
            while True:
                client_socket, client_address = server_socket.accept()
                print(f"New Minecraft client: {client_address}")
                
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except Exception as e:
            print(f"Server error: {e}")

tunnel = MinecraftTunnel()

@app.route('/')
def home():
    return {
        "status": "Minecraft Tunnel Server is running",
        "minecraft_server": f"{MINECRAFT_SERVER_HOST}:{MINECRAFT_SERVER_PORT}",
        "tunnel_port": TUNNEL_PORT
    }

@app.route('/health')
def health():
    return {"status": "healthy"}

def start_tunnel():
    time.sleep(2)
    tunnel.start_tunnel_server()

if __name__ == "__main__":
    tunnel_thread = threading.Thread(target=start_tunnel)
    tunnel_thread.daemon = True
    tunnel_thread.start()
    app.run(host='0.0.0.0', port=8080, debug=False)
