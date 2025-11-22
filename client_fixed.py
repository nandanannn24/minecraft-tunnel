import socket
import threading
import time
import sys

class TunnelClient:
    def __init__(self, railway_url, local_host='localhost', local_port=25566, remote_port=25565):  # ← UBAH ke 25565
        self.railway_url = railway_url.replace('https://', '').replace('http://', '').split(':')[0]
        self.remote_port = remote_port
        self.local_host = local_host
        self.local_port = local_port
        self.running = False
        
    def handle_connection(self, client_socket, client_address):
        try:
            print(f"🔄 Connecting to Railway: {self.railway_url}:{self.remote_port}")
            
            # Connect ke Railway di port 25565
            railway_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            railway_socket.settimeout(30)
            railway_socket.connect((self.railway_url, self.remote_port))
            
            print(f"✅ Tunnel connected for {client_address}")
            
            # Connect ke Minecraft server lokal
            minecraft_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            minecraft_socket.settimeout(30)
            minecraft_socket.connect(('localhost', 25565))
            
            print(f"✅ Connected to local Minecraft server")
            
            # Forward data
            def forward_to_minecraft():
                try:
                    while True:
                        data = railway_socket.recv(4096)
                        if not data:
                            break
                        minecraft_socket.sendall(data)
                except Exception as e:
                    print(f"❌ Error forwarding to minecraft: {e}")
            
            def forward_to_railway():
                try:
                    while True:
                        data = minecraft_socket.recv(4096)
                        if not data:
                            break
                        railway_socket.sendall(data)
                except Exception as e:
                    print(f"❌ Error forwarding to railway: {e}")
            
            thread1 = threading.Thread(target=forward_to_minecraft)
            thread2 = threading.Thread(target=forward_to_railway)
            
            thread1.daemon = True
            thread2.daemon = True
            
            thread1.start()
            thread2.start()
            
            thread1.join()
            thread2.join()
            
        except Exception as e:
            print(f"❌ Tunnel error: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
            try:
                railway_socket.close()
            except:
                pass
            try:
                minecraft_socket.close()
            except:
                pass
    
    def start(self):
        self.running = True
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((self.local_host, self.local_port))
            server_socket.listen(5)
            print(f"🎮 Minecraft Bridge running on {self.local_host}:{self.local_port}")
            print(f"🔗 Connected to Railway: {self.railway_url}:{self.remote_port}")
            print("⏹️  Press Ctrl+C to stop")
            print("")
            print("📝 Untuk teman:")
            print(f"   Server Address: {self.railway_url}")
            print("   Port: 25565")
            print("")
            
            while self.running:
                try:
                    client_socket, client_address = server_socket.accept()
                    print(f"🔌 Bridge connection from {client_address}")
                    
                    client_thread = threading.Thread(
                        target=self.handle_connection,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        print(f"❌ Bridge error: {e}")
                    
        except Exception as e:
            print(f"❌ Client error: {e}")
        finally:
            server_socket.close()

if __name__ == "__main__":
    RAILWAY_URL = "minecraft-tunnel-production.up.railway.app"
    
    print("🚀 Starting Minecraft Bridge Client...")
    print("🔧 Menggunakan port 25565 di Railway...")
    time.sleep(2)
    
    # Test koneksi ke port 25565 di Railway
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(10)
        result = test_socket.connect_ex((RAILWAY_URL.replace('https://', '').replace('http://', ''), 25565))
        if result == 0:
            print("✅ Railway port 25565: OPEN")
        else:
            print(f"❌ Railway port 25565: CLOSED (error {result})")
            print("💡 Pastikan di Railway:")
            print("   - Environment variable PORT = 25565")
            print("   - Networking untuk port 25565 sudah aktif")
        test_socket.close()
    except Exception as e:
        print(f"❌ Connection test error: {e}")
    
    client = TunnelClient(RAILWAY_URL, remote_port=25565)  # ← PASTIKAN 25565 di sini
    
    try:
        client.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down bridge client...")
        client.running = False
    except Exception as e:
        print(f"❌ Fatal error: {e}")
