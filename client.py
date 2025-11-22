import socket
import threading
import requests
import time

class TunnelClient:
    def __init__(self, railway_url, local_host='localhost', local_port=25565):
        self.railway_url = railway_url.replace('https://', '').replace('http://', '')
        self.local_host = local_host
        self.local_port = local_port
        self.running = False
        
    def handle_connection(self, client_socket, client_address):
        try:
            # Connect ke server Railway
            railway_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            railway_socket.connect((self.railway_url, 25565))
            
            print(f"Tunnel established for {client_address}")
            
            # Forward data bidirectional
            def forward_to_railway():
                try:
                    while True:
                        data = client_socket.recv(4096)
                        if not data:
                            break
                        railway_socket.sendall(data)
                except:
                    pass
            
            def forward_to_client():
                try:
                    while True:
                        data = railway_socket.recv(4096)
                        if not data:
                            break
                        client_socket.sendall(data)
                except:
                    pass
            
            thread1 = threading.Thread(target=forward_to_railway)
            thread2 = threading.Thread(target=forward_to_client)
            
            thread1.start()
            thread2.start()
            
            thread1.join()
            thread2.join()
            
        except Exception as e:
            print(f"Error in tunnel: {e}")
        finally:
            client_socket.close()
            railway_socket.close()
    
    def start(self):
        self.running = True
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((self.local_host, self.local_port))
            server_socket.listen(5)
            print(f"Client tunnel listening on {self.local_host}:{self.local_port}")
            print(f"Forwarding to Railway: {self.railway_url}")
            
            while self.running:
                client_socket, client_address = server_socket.accept()
                print(f"New Minecraft connection from {client_address}")
                
                client_thread = threading.Thread(
                    target=self.handle_connection,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            server_socket.close()

if __name__ == "__main__":
    # Ganti dengan URL Railway kamu
    RAILWAY_URL = "minecraft-tunnel-production.up.railway.app"  # Ganti dengan URL Railway-mu
    
    client = TunnelClient(RAILWAY_URL)
    
    try:
        client.start()
    except KeyboardInterrupt:
        print("Shutting down...")
        client.running = False
