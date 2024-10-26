import network
import socket
import time

# Connect to Wi-Fi
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        print('Connecting to network...')
        time.sleep(1)
    print('Network connected!')
    print('IP address:', wlan.ifconfig()[0])

# Start the server
def start_server():
    addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Listening on', addr)

    while True:
        cl, addr = s.accept()
        print('Client connected from', addr)
        cl.send('Welcome to the ESP32 server!'.encode())
        cl.close()

# Replace with your Wi-Fi credentials
SSID = 'BorgoPio138'
PASSWORD = 'buongiorno'

connect_wifi(SSID, PASSWORD)
start_server()