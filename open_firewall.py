import subprocess
import sys
import os

def run_as_admin():
    """Jalankan script sebagai administrator"""
    if sys.platform.startswith('win'):
        try:
            # Cek apakah sudah running sebagai admin
            if os.getuid() == 0:
                return True
        except AttributeError:
            import ctypes
            if ctypes.windll.shell32.IsUserAnAdmin():
                return True
        
        # Jika bukan admin, restart dengan admin privileges
        print("Script membutuhkan hak administrator...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)

def open_minecraft_port():
    """Buka port 25565 di Windows Firewall"""
    try:
        # Rule untuk TCP
        tcp_command = [
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            'name="Minecraft Server TCP"',
            'dir=in',
            'action=allow',
            'protocol=TCP',
            'localport=25565'
        ]
        
        # Rule untuk UDP
        udp_command = [
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            'name="Minecraft Server UDP"',
            'dir=in',
            'action=allow',
            'protocol=UDP',
            'localport=25565'
        ]
        
        print("Membuka port 25565 di Windows Firewall...")
        
        # Eksekusi commands
        subprocess.run(tcp_command, check=True, capture_output=True)
        print("✓ Rule TCP berhasil ditambahkan")
        
        subprocess.run(udp_command, check=True, capture_output=True)
        print("✓ Rule UDP berhasil ditambahkan")
        
        print("\nPort 25565 berhasil dibuka!")
        print("Sekarang Minecraft server bisa diakses dari jaringan lain")
        
    except subprocess.CalledProcessError as e:
        print(f"Error: Gagal menambahkan rule firewall")
        print("Pastikan script dijalankan sebagai Administrator")
    except Exception as e:
        print(f"Error: {e}")

def check_existing_rules():
    """Cek apakah rule sudah ada"""
    try:
        result = subprocess.run(
            ['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name=all'],
            capture_output=True, text=True
        )
        return "Minecraft Server" in result.stdout
    except:
        return False

if __name__ == "__main__":
    if sys.platform.startswith('win'):
        run_as_admin()
        open_minecraft_port()
        
        # Test port
        print("\nTesting port 25565...")
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', 25565))
            print("✓ Port 25565 tersedia dan bisa digunakan")
            sock.close()
        except OSError as e:
            print(f"✗ Port 25565 sedang digunakan: {e}")
    else:
        print("Script ini hanya untuk Windows")