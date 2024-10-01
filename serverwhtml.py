import network
import socket
from machine import Pin, UART
import time
import os

# Replace with your network credentials
ssid = 'StewartNet'
password = 'trawet07'

# Connect to Wi-Fi
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

while not station.isconnected():
    pass

print('Connection successful')
print(station.ifconfig())

# Set up the built-in LED pin
led = Pin(2, Pin.OUT)

# HTML content
html = """<!DOCTYPE html>
<html>
<head>
    <title>ESP32 Control</title>
    <style>
        button {
            font-size: 3em; /* 3 times bigger */
            padding: 20px;
            margin: 10px;
        }
    </style>
</head>
<body>
    <h1>ESP32 Master Control</h1>
    <button onclick="sendCommand('on')">Turn LED On</button>
    <button onclick="sendCommand('off')">Turn LED Off</button>
    <button onclick="sendCommand('blink')">Blink LED</button>
    <button onclick="sendCommand('list')">List Files</button>
    <button onclick="sendCommand('send')">Send File to Serial</button>

    <script>
        function sendCommand(command) {
            fetch(`http://${window.location.hostname}/command?cmd=${command}`)
                .then(response => response.text())
                .then(data => {
                    console.log(data);
                    if (command === 'list') {
                        alert(data); // Display the file list as is
                    }
                });
        }
    </script>
</body>
</html>
"""

# Function to send a file to serial
def send_to_serial(file_name):
    uart = UART(1, baudrate=9600, tx=16, rx=17)  # Adjust pins and baudrate as needed
    XON = 0x11
    XOFF = 0x13
    flow_control = True

    try:
        with open(file_name, 'rb') as f:
            # Prepend the XON character
            uart.write(bytes([XON]))
            while True:
                chunk = f.read(1024)
                if not chunk:
                    break
                for byte in chunk:
                    while not flow_control:
                        if uart.any():
                            control_char = uart.read(1)
                            if control_char == bytes([XOFF]):
                                flow_control = False
                            elif control_char == bytes([XON]):
                                flow_control = True
                        time.sleep(0.01)  # Small delay to prevent busy waiting
                    uart.write(bytes([byte]))
        print(f'File {file_name} sent to serial device')
    except OSError as e:
        print(f"Error sending file {file_name}: {e}")

# Set up the web server
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reuse the address
s.bind(addr)
s.listen(1)

print('Listening on', addr)

def handle_request(client):
    request = client.recv(1024)
    request = str(request)
    cmd_on = request.find('/command?cmd=on')
    cmd_off = request.find('/command?cmd=off')
    cmd_blink = request.find('/command?cmd=blink')
    cmd_list = request.find('/command?cmd=list')
    cmd_send = request.find('/command?cmd=send')

    if cmd_on != -1:
        led.value(1)  # Turn the LED on
    if cmd_off != -1:
        led.value(0)  # Turn the LED off
    if cmd_blink != -1:
        for _ in range(5):
            led.value(1)  # Turn the LED on
            time.sleep(0.5)
            led.value(0)  # Turn the LED off
            time.sleep(0.5)
    if cmd_list != -1:
        files = os.listdir()
        response = '<br>'.join(files)
        client.send('HTTP/1.1 200 OK\r\n')
        client.send('Content-Type: text/plain\r\n')
        client.send('Connection: close\r\n\r\n')
        client.sendall(response)
        client.close()
        return
    if cmd_send != -1:
        file_name = 'example.txt'  # Replace with the actual file name you want to send
        send_to_serial(file_name)
        response = f'File {file_name} sent to serial device'
        client.send('HTTP/1.1 200 OK\r\n')
        client.send('Content-Type: text/plain\r\n')
        client.send('Connection: close\r\n\r\n')
        client.sendall(response)
        client.close()
        return

    response = html
    client.send('HTTP/1.1 200 OK\r\n')
    client.send('Content-Type: text/html\r\n')
    client.send('Connection: close\r\n\r\n')
    client.sendall(response)
    client.close()

try:
    while True:
        client, addr = s.accept()
        print('Client connected from', addr)
        handle_request(client)
except Exception as e:
    print('Error:', e)
finally:
    s.close()  # Ensure the socket is closed