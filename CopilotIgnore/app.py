"""
General: This content works but functionality is limited.
Need to now begin to add commands that call the functionality of the server.
See startup sequence text file in directory for more information.

Planned changes and status:
1. Add status box to the index.html page to display the status of the server. - Not started
2. Add pull down menu to the index.html page to select the file to be send to the ESP32. - Not started
3. Add pull down menu to the index.html page to select the file to be deleted from the ESP32. - Not started
4. Add pull down menu to the index.html page to select the machine being used. - Not started
5. Changed app.py to also bind to the LAN IP address of the computer hosting it. - Completed
6. Add all other relevant commands to the index.html code to duplicate the functionality of the client . - Not started
"""

from flask import Flask, render_template, request, jsonify, Response
import socket
import threading

app = Flask(__name__)

ESP32_IP = '192.168.1.120'  # Replace with the actual IP address of your ESP32
ESP32_PORT = 8080

clients = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_file_list', methods=['GET'])
def update_file_list():
    files = send_command_to_esp32('LIST_FILES')
    send_status_message('File list updated')
    return jsonify(files)

@app.route('/send_file', methods=['POST'])
def send_file():
    file_path = request.form['file_path']
    send_command_to_esp32(f'SEND_FILE {file_path}')
    send_status_message(f'File {file_path} sent')
    return 'File sent'

@app.route('/delete_file', methods=['POST'])
def delete_file():
    file_name = request.form['file_name']
    send_command_to_esp32(f'DELETE_FILE {file_name}')
    send_status_message(f'File {file_name} deleted')
    return 'File deleted'

@app.route('/receive_message', methods=['POST'])
def receive_message():
    message = request.json.get('message')
    send_status_message(message)
    return 'Message received', 200

@app.route('/events')
def events():
    def event_stream():
        while True:
            if clients:
                message = clients.pop(0)
                yield f'data: {message}\n\n'
    return Response(event_stream(), mimetype='text/event-stream')

def send_command_to_esp32(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ESP32_IP, ESP32_PORT))
        s.sendall(command.encode())

def send_status_message(message):
    clients.append(message)

if __name__ == '__main__':
    app.run(debug=True, host='192.168.1.109', port=5000)