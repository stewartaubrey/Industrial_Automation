import socket
import time
import network
from machine import UART, reset
import uos

HOST = '192.168.1.120'
PORT = 8080

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    ip = '192.168.1.120'
    subnet = '255.255.255.0'
    gateway = '192.168.1.1'
    dns = '8.8.8.8'
    wlan.ifconfig((ip, subnet, gateway, dns))
    wlan.connect(ssid, password)
    
    while not wlan.isconnected():
        print('Connecting to network...')
        time.sleep(1)
    
    print('Network connected!')
    print('IP address:', wlan.ifconfig()[0])

def receive_from_serial(file_name):
    #time.sleep(0)
    uart = UART(1, baudrate=9600,tx=16, rx=17)  # Adjust pins and baudrate as needed
    #print("just before try loop")
    try:
        #print("inside try loop")
        #print(file_name)
        with open(file_name, 'wb') as f:
            while True:
                #print("inside True loop")
                chunk = uart.read(1024)
                time.sleep(.5)
                print(chunk)
                if chunk:
                    f.write(chunk)
                    print(chunk)
                    #time.sleep(.1)
                    #if (b'%' or b'M30') in chunk:
                    if (b'M30') in chunk:
                      break
                    if not chunk:
                        count=0
                        if count>=20:
                            break
                            count+=1
                            print(20-count, "timeout counter")
                        print("No more serial data",count)
                        #break
        print(f'Data received from serial com1 and saved to {file_name}')
    except OSError as e:
        print(f"Error receiving data from serial: {e}")

def delete_file(file_name):
    try:
        uos.remove(file_name)
        print(f'File {file_name} deleted')
    except OSError as e:
        print(f"Error deleting file {file_name}: {e}")

def send_to_serial(file_name): #no xon/xoff
    uart = UART(1, baudrate=9600, tx=16, rx=17, bits=8, parity=None, stop=1)  # Adjust pins and baudrate as needed

    try:
        with open(file_name, 'rb') as f:
            while True:
                chunk = f.read(1024)
                if not chunk:
                    break
                uart.write(chunk)
        print(f'File {file_name} sent to serial device')
    except OSError as e:
        print(f"Error sending file {file_name}: {e}")

def send_to_serialXon(file_name): #with xon/xoff
    uart = UART(1, baudrate=9600, tx=16, rx=17)  # Adjust pins and baudrate as needed
    XON = 0x26
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

def handle_request(client):
    try:
        request = client.recv(1024).decode('utf-8')
        request_line = request.split('\n')[0]
        parts = request_line.split()
        
        if len(parts) < 3:
            raise ValueError("Invalid HTTP request line")

        method, path, _ = parts

        if method == 'GET' and path == '/':
            response = """HTTP/1.1 200 OK
Content-Type: text/html

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Server Control Panel</title>
    <style>
        body { display: flex; flex-direction: column; align-items: center; }
        .container {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 100%;
            max-width: 500px;
        }
        button, input { 
            margin: 10px; 
            padding: 10px; 
            width: 200px; 
            font-size: 20px; /* Added this line to increase text size */
        }
        h1 { text-align: center; }
    </style>
    <script>
        async function sendCommand(endpoint, data = {}) {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams(data)
            });
            const result = await response.json();
            alert(result.status);
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>STEWART INDUSTRIAL AUTOMATION</h1>
        <button onclick="sendCommand('/connect_wifi')">Connect to WiFi</button>
        <button onclick="sendCommand('/start_server')">Start Server</button>
        <input type="text" id="statusMessage" placeholder="Enter status message">
        <button onclick="sendCommand('/send_status', {message: document.getElementById('statusMessage').value})">Send Status Message</button>
        <button onclick="sendCommand('/clear_files')">Clear Files</button>
        <button onclick="sendCommand('/list_files')">List Files</button>
        <button onclick="sendCommand('/receive_serial')">Receive Serial Data</button>
        <button onclick="sendCommand('/send_serial_xon')">Send Serial Data (XON/XOFF)</button>
    </div>
</body>
</html>
"""            
            client.send(response.encode('utf-8'))
        elif method == 'POST':
            if path == '/connect_wifi':
                connect_wifi(ssid, password)
                response = '{"status": "WiFi connected"}'
            elif path == '/start_server':
                response = '{"status": "Server started"}'
            elif path == '/send_status':
                message = request.split('\r\n\r\n')[1].split('=')[1]
                send_status_message(client, message)
                response = '{"status": "Status message sent"}'
            elif path == '/clear_files':
                clear_files()
                response = '{"status": "Files cleared"}'
            elif path == '/list_files':
                list_files(client)
                response = '{"status": "File list sent"}'
            elif path == '/receive_serial':
                receive_from_serial('serial_data.txt')
                response = '{"status": "Serial data received"}'
            elif path == '/send_serial_xon':
                send_to_serialXon('serial_data.txt')
                response = '{"status": "File sent to serial device with XON/XOFF"}'
            else:
                response = '{"status": "Unknown command"}'
            
            client.send(f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{response}".encode('utf-8'))
    except Exception as e:
        response = f"HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nError: {e}"
        client.send(response.encode('utf-8'))
    finally:
        client.close()
def run():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 5000))
    server_socket.listen(1)
    print('Starting server on port 5000...')

    while True:
        client, addr = server_socket.accept()
        handle_request(client)

if __name__ == '__main__':
    run()
