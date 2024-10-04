import network
import socket
import os
import ujson
from machine import UART

# Connect to WiFi
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        pass
    print('Network connected:', wlan.ifconfig())

# List files in the directory
def list_files(directory='.'):
    return [f for f in os.listdir(directory) if os.path.isfile(f)]

# Send file to serial
def send_to_serial(file_name):
    uart = UART(1, baudrate=9600, tx=16, rx=17)  # Adjust pins and baudrate as needed
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

# HTML content
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Server Control Panel</title>
    <style>
        body { display: flex; flex-direction: column; align-items: center; }
        .container {
            display: flex; flex-direction: column;
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

        async function fetchFiles() {
            const response = await fetch('/list_files');
            const files = await response.json();
            const select = document.getElementById('fileSelect');
            files.forEach(file => {
                const option = document.createElement('option');
                option.value = file;
                option.textContent = file;
                select.appendChild(option);
            });
        }

        async function sendFile() {
            const file = document.getElementById('fileSelect').value;
            await sendCommand('/send_file', { file });
        }

        window.onload = fetchFiles;
    </script>
</head>
<body>
    <div class="container">
        <h1>STEWART INDUSTRIAL AUTOMATION</h1>
        <button onclick="sendCommand('/connect_wifi')">Connect to WiFi</button>
        <button onclick="sendCommand('/start_server')">Start Server</button>
        <label for="fileSelect">Choose a file:</label>
        <select id="fileSelect">
            <!-- Options will be populated by the backend -->
        </select>
        <button onclick="sendFile()">Send File to Serial</button>
    </div>
</body>
</html>
"""

# Handle HTTP requests
def handle_request(client):
    request = client.recv(1024).decode('utf-8')
    if 'GET / ' in request:
        client.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n' + html_content)
    elif 'GET /list_files' in request:
        files = list_files()
        response = ujson.dumps(files)
        client.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n' + response)
    elif 'POST /send_file' in request:
        length = int(request.split('Content-Length: ')[1].split('\r\n')[0])
        body = client.recv(length).decode('utf-8')
        file_name = body.split('=')[1]
        send_to_serial(file_name)
        response = ujson.dumps({'status': f'File {file_name} sent to serial device'})
        client.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n' + response)
    client.close()

# Start the web server
def start_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reuse the address
    s.bind(addr)
    s.listen(5)
    print('Listening on', addr)
    while True:
        client, addr = s.accept()
        handle_request(client)

# Main function
def main():
    ssid = 'your-ssid'
    password = 'your-password'
    connect_wifi(ssid, password)
    start_server()

if __name__ == '__main__':
    main()