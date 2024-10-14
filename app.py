from flask import Flask, render_template, request, jsonify
import socket

app = Flask(__name__)

ESP32_IP = '192.168.1.120'  # Replace with the actual IP address of your ESP32
ESP32_PORT = 8080

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_file_list', methods=['GET'])
def update_file_list():
    files = send_command_to_esp32('LIST_FILES')
    return jsonify(files)

@app.route('/send_file', methods=['POST'])
def send_file():
    file_path = request.form['file_path']
    send_command_to_esp32(f'SEND_FILE {file_path}')
    return 'File sent'

@app.route('/delete_file', methods=['POST'])
def delete_file():
    file_name = request.form['file_name']
    send_command_to_esp32(f'DELETE_FILE {file_name}')
    return 'File deleted'

def send_command_to_esp32(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ESP32_IP, ESP32_PORT))
        s.sendall(command.encode())
        response = s.recv(4096).decode()
    return response

if __name__ == '__main__':
    app.run(debug=True)