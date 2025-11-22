@echo off
echo Membuka port 25565 di Windows Firewall untuk Minecraft...
netsh advfirewall firewall add rule name="Minecraft Server TCP" dir=in action=allow protocol=TCP localport=25565
netsh advfirewall firewall add rule name="Minecraft Server UDP" dir=in action=allow protocol=UDP localport=25565
echo Port 25565 telah dibuka!
pause