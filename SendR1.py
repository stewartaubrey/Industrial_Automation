import socket

def upload_file(server_ip, server_port, file_name):
    try:
        s = socket.socket()
        s.connect((server_ip, server_port))
        s.send(f'UPLOAD_FILE {file_name}'.encode())
        
        with open(file_name, 'rb') as f:
            while True:
                chunk = f.read(1024)
                if not chunk:
                    break
                s.send(chunk)
        
        # Wait for the acknowledgment
        ack = s.recv(1024)
        if ack == b'UPLOAD_SUCCESS':
            print(f'File {file_name} uploaded successfully')
        else:
            print(f'Failed to upload file {file_name}')
        
        s.close()
    except OSError as e:
        print(f"Error uploading file {file_name}: {e}")

def refresh_file_list(server_ip, server_port):
    try:
        s = socket.socket()
        s.connect((server_ip, server_port))
        s.send(b'LIST_FILES')
        file_list = s.recv(4096).decode()
        print(f'Files on ESP32:\n{file_list}')
        s.close()
    except OSError as e:
        print(f"Error refreshing file list: {e}")

def clear_files(server_ip, server_port):
    try:
        s = socket.socket()
        s.connect((server_ip, server_port))
        s.send(b'CLEAR_FILES')
        print('Files cleared on ESP32')
        s.close()
    except OSError as e:
        print(f"Error clearing files: {e}")

def reboot_esp32(server_ip, server_port):
    try:
        s = socket.socket()
        s.connect((server_ip, server_port))
        s.send(b'REBOOT')
        print('ESP32 rebooted')
        s.close()
    except OSError as e:
        print(f"Error rebooting ESP32: {e}")

# Example usage
server_ip = '192.168.1.120'
server_port = 8080
file_name = 'example.txt'

# Upload a file
upload_file(server_ip, server_port, file_name)

# Refresh file list on ESP32
refresh_file_list(server_ip, server_port)

# Clear files on ESP32
clear_files(server_ip, server_port)

# Reboot ESP32
reboot_esp32(server_ip, server_port)