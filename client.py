import socket
import threading
import sys
import time

class TunnelClient:
    def __init__(self, railway_url, local_host='localhost', local_port=25565, remote_port=25565):
        self.railway_url = railway_url.replace('https://', '').replace('http://', '').split(':')[0]
        self.remote_port = remote_port
        self.local_host = local_host
        self.local_port = local_port
        self.running = False
        
    def handle_connection(self, client_socket, client_address):
        try:
            print(f"🔄 Connecting to Railway: {self.railway_url}:{self.remote_port}")
            
            # Connect ke server Railway
            railway_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            railway_socket.settimeout(30)
            railway_socket.connect((self.railway_url, self.remote_port))
            
            print(f"✅ Tunnel established for {client_address}")
            
            # Forward data bidirectional
            def forward_to_railway():
                try:
                    while True:
                        data = client_socket.recv(4096)
                        if not data:
                            break
                        railway_socket.sendall(data)
                except Exception as e:
                    print(f"❌ Error forwarding to railway: {e}")
            
            def forward_to_client():
                try:
                    while True:
                        data = railway_socket.recv(4096)
                        if not data:
                            break
                        client_socket.sendall(data)
                except Exception as e:
                    print(f"❌ Error forwarding to client: {e}")
            
            thread1 = threading.Thread(target=forward_to_railway)
            thread2 = threading.Thread(target=forward_to_client)
            
            thread1.daemon = True
            thread2.daemon = True
            
            thread1.start()
            thread2.start()
            
            thread1.join()
            thread2.join()
            
        except Exception as e:
            print(f"❌ Error in tunnel: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
            try:
                railway_socket.close()
            except:
                pass
    
    def start(self):
        self.running = True
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((self.local_host, self.local_port))
            server_socket.listen(5)
            print(f"🎮 Minecraft Client Tunnel running on {self.local_host}:{self.local_port}")
            print(f"🔗 Forwarding to: {self.railway_url}:{self.remote_port}")
            print("⏹️  Press Ctrl+C to stop")
            print("")
            print("📝 Pastikan:")
            print("  1. Minecraft server sudah jalan di komputermu")
            print("  2. Port 25565 sudah terbuka di firewall")
            print("  3. Teman connect ke: " + self.railway_url)
            print("")
            
            while self.running:
                try:
                    client_socket, client_address = server_socket.accept()
                    print(f"🔌 New Minecraft connection from {client_address}")
                    
                    client_thread = threading.Thread(
                        target=self.handle_connection,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        print(f"❌ Accept error: {e}")
                    
        except Exception as e:
            print(f"❌ Client error: {e}")
        finally:
            server_socket.close()

if __name__ == "__main__":
    # Ganti dengan URL Railway kamu
    RAILWAY_URL = "minecraft-tunnel-production.up.railway.app"
    
    print("🚀 Starting Minecraft Tunnel Client...")
    time.sleep(1)
    
    client = TunnelClient(RAILWAY_URL)
    
    try:
        client.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down tunnel client...")
        client.running = False
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        print("💡 Tips:")
        print("  - Pastikan URL Railway benar")
        print("  - Pastikan internet terhubung")
        print("  - Coba restart client.py")
