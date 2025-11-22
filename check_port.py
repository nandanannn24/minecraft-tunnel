import socket
import subprocess

def check_port_open():
    """Cek apakah port 25565 terbuka"""
    try:
        # Cek dari local
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 25565))
        sock.close()
        
        if result == 0:
            print("✓ Port 25565 terbuka di localhost")
        else:
            print("✗ Port 25565 tertutup di localhost")
            
    except Exception as e:
        print(f"Error checking port: {e}")

def check_firewall_rules():
    """Cek firewall rules untuk Minecraft"""
    try:
        result = subprocess.run(
            ['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name=all'],
            capture_output=True, text=True, encoding='utf-8'
        )
        
        if "Minecraft Server" in result.stdout:
            print("✓ Firewall rules untuk Minecraft ditemukan")
        else:
            print("✗ Firewall rules untuk Minecraft tidak ditemukan")
            
    except Exception as e:
        print(f"Error checking firewall: {e}")

if __name__ == "__main__":
    print("Memeriksa konfigurasi port Minecraft...")
    check_port_open()
    check_firewall_rules()