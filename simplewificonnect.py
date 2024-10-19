import network
import socket
import time

# WiFi credentials
SSID = "San Pietro all’Orto 6-P.2"
PASSWORD = 'wearehappy'
#SSID = "stewa's iPhone"
#PASSWORD = 'trawet07'



# Initialize WiFi connection
wlan = network.WLAN(network.STA_IF)
#wlan.disconnect()
wlan.active(False)
wlan.active(True)

# Connect to WiFi network
wlan.connect(SSID, PASSWORD)

# Wait for connection
while not wlan.isconnected():
    time.sleep(1)

# Get IP address
ip = wlan.ifconfig()[0]
port = wlan.ifconfig()[2]

# Print WiFi connection info
ip, subnet, gateway, dns = wlan.ifconfig()
port = 80
print(f"Connected to WiFi network {SSID}")
print(f"IP Address: {ip}")
print(f"Subnet Mask: {subnet}")
print(f"Gateway: {gateway}")
print(f"DNS: {dns}")
print(f"Port: {port}")

# Close the connection
wlan.disconnect()
wlan.active(False)