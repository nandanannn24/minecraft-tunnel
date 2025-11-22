import os
from flask import Flask, request, jsonify
import socket
import threading
import time
from threading import Lock
import logging

app = Flask(__name__)

# Konfigurasi dari Environment Variables (Railway)
MINECRAFT_SERVER_HOST = os.environ.get('MINECRAFT_HOST', 'localhost')
MINECRAFT_SERVER_PORT = int(os.environ.get('MINECRAFT_PORT', '25565'))
TUNNEL_PORT = int(os.environ.get('PORT', '25565'))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MinecraftTunnel:
    def __init__(self):
        self.connections = {}
        self.lock = Lock()
        
    def handle_client(self, client_socket, client_address):
        try:
            logger.info(f"🔗 New Minecraft client connection from {client_address}")
            
            # Connect ke server Minecraft lokal via client tunnel
            minecraft_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            minecraft_socket.settimeout(10)
            
            logger.info(f"🔄 Connecting to Minecraft server at {MINECRAFT_SERVER_HOST}:{MINECRAFT_SERVER_PORT}")
            minecraft_socket.connect((MINECRAFT_SERVER_HOST, MINECRAFT_SERVER_PORT))
            logger.info(f"✅ Connected to Minecraft server")
            
            # Simpan connection
            with self.lock:
                self.connections[client_address] = {
                    'client': client_socket,
                    'minecraft': minecraft_socket
                }
            
            # Forward data bidirectional dengan error handling
            def forward_to_minecraft():
                try:
                    while True:
                        data = client_socket.recv(4096)
                        if not data:
                            break
                        minecraft_socket.sendall(data)
                except Exception as e:
                    logger.error(f"❌ Error forwarding to minecraft: {e}")
                finally:
                    try:
                        client_socket.close()
                    except:
                        pass
            
            def forward_to_client():
                try:
                    while True:
                        data = minecraft_socket.recv(4096)
                        if not data:
                            break
                        client_socket.sendall(data)
                except Exception as e:
                    logger.error(f"❌ Error forwarding to client: {e}")
                finally:
                    try:
                        minecraft_socket.close()
                    except:
                        pass
            
            # Jalankan thread untuk forwarding
            thread1 = threading.Thread(target=forward_to_minecraft)
            thread2 = threading.Thread(target=forward_to_client)
            
            thread1.daemon = True
            thread2.daemon = True
            
            thread1.start()
            thread2.start()
            
            thread1.join()
            thread2.join()
            
        except Exception as e:
            logger.error(f"❌ Error handling client {client_address}: {e}")
        finally:
            # Cleanup
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
            logger.info(f"🔌 Connection closed for {client_address}")

    def start_tunnel_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.settimeout(1)  # Timeout untuk graceful shutdown
        
        try:
            server_socket.bind(('0.0.0.0', TUNNEL_PORT))
            server_socket.listen(10)
            logger.info(f"🚀 Minecraft Tunnel Server started on port {TUNNEL_PORT}")
            logger.info(f"🎯 Forwarding to: {MINECRAFT_SERVER_HOST}:{MINECRAFT_SERVER_PORT}")
            
            while True:
                try:
                    client_socket, client_address = server_socket.accept()
                    logger.info(f"🔌 New connection from {client_address}")
                    
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"❌ Server accept error: {e}")
                    break
                
        except Exception as e:
            logger.error(f"❌ Tunnel server error: {e}")
        finally:
            server_socket.close()
            logger.info("🛑 Tunnel server stopped")

# Jalankan tunnel server
tunnel = MinecraftTunnel()

@app.route('/')
def home():
    return jsonify({
        "status": "Minecraft Tunnel Server is running",
        "minecraft_server": f"{MINECRAFT_SERVER_HOST}:{MINECRAFT_SERVER_PORT}",
        "tunnel_port": TUNNEL_PORT,
        "active_connections": len(tunnel.connections)
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "connections": len(tunnel.connections)
    })

def start_tunnel():
    time.sleep(2)  # Tunggu Flask start
    tunnel.start_tunnel_server()

if __name__ == "__main__":
    logger.info("🎮 Starting Minecraft Tunnel Server...")
    
    # Jalankan tunnel server di thread terpisah
    tunnel_thread = threading.Thread(target=start_tunnel)
    tunnel_thread.daemon = True
    tunnel_thread.start()
    
    # Jalankan Flask app
    web_port = 8080
    logger.info(f"🌐 Web dashboard running on port {web_port}")
    app.run(host='0.0.0.0', port=web_port, debug=False, threaded=True)
