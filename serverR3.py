""" This program runs on a ESP32 connected
    via serial link to the CNC machine
    
    Next upgrade is setup messaging back to client:
    1. Send connection status and info
    2. Send message confirming command receipt

Changed the send_to_serial function prepend the XON character to the file data before sending it to the CNC machine.

"""

import network
import socket
import time
from machine import UART, reset 
import uos

ssid='StewartNet'
password='trawet07'

def send_status_message(client, message):
    try:
        client.sendall(f'STATUS_MESSAGE {message}'.encode())
    except OSError as e:
        print(f"Error sending status message: {e}")


def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    time.sleep(1)
    wlan.active(True)
    time.sleep(1)
    # Set static IP address
    ip = '192.168.1.120'
    subnet = '255.255.255.0'
    gateway = '192.168.1.1'
    dns = '8.8.8.8'
    wlan.ifconfig((ip, subnet, gateway, dns))
    time.sleep(1)
    wlan.connect(ssid, password)
    
    while not wlan.isconnected():
        print('Connecting to network...')
        time.sleep(1)
    
    print('Network connected!')
    print('IP address:', wlan.ifconfig()[0])
    
def start_server():
    addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    s.settimeout(30)  # Increase the timeout period to 30 seconds
    print('Listening on', addr)
    
    while True:
        try:
            cl, addr = s.accept()
            print('Client connected from', addr)
            data = cl.recv(1024)
            if data == b'CLEAR_FILES':
                clear_files()
                send_status_message(cl, 'All files cleared on ESP32')
            elif data == b'LIST_FILES':
                list_files(cl)
                send_status_message(cl, 'File list sent to client')
            elif data.startswith(b'SEND_FILE'):
                file_name = data[len('SEND_FILE '):].decode()
                send_to_serial(file_name)
                send_status_message(cl, f'File {file_name} sent to CNC')
            elif data.startswith(b'DELETE_FILE'):
                file_name = data[len('DELETE_FILE '):].decode()
                delete_file(file_name)
                send_status_message(cl, f'File {file_name} deleted from ESP32')
            elif data.startswith(b'RECEIVE_FILE'):
                file_name = data[len('RECEIVE_FILE '):].decode()
                send_file_to_client(cl, file_name)
                send_status_message(cl, f'File {file_name} sent to client')
            elif data == b'REBOOT':
                send_status_message(cl, 'Reboot command received')
                cl.close()
                print('Reboot command received')
                reset()  # Reboot the ESP32
            elif data == b'RECEIVE_SERIAL':
                receive_from_serial('serial_data.txt')  # Save serial data to 'serial_data.txt'
                send_status_message(cl, 'Serial data received and saved')
            else:
                file_name, file_data = data.split(b'\n', 1)
                file_name = file_name.decode()
                
                file_path = file_name
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                    while True:
                        data = cl.recv(1024)
                        if not data:
                            break
                        f.write(data)
                send_status_message(cl, f'File {file_name} received and saved to {file_path}')
                cl.close()
                print(f'File {file_name} received and saved to {file_path}')
        except OSError as e:
            if e.args[0] == 116:  # ETIMEDOUT error code
                print('Socket timeout, no client connected')
            else:
                print(f"Error: {e}")


def send_to_serial(file_name):
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

def clear_files():
    try:
        for item in uos.listdir():
            if uos.stat(item)[0] & 0x4000:  # Check if it's a directory
                for file in uos.listdir(item):
                    if not file.endswith('.py'):
                        try:
                            uos.remove(f"{item}/{file}")
                            print(f"Removed file: {item}/{file}")
                        except OSError as e:
                            print(f"Error removing file {item}/{file}: {e}")
                try:
                    uos.rmdir(item)
                    print(f"Removed directory: {item}")
                except OSError as e:
                    print(f"Error removing directory {item}: {e}")
            elif not item.endswith('.py'):
                try:
                    uos.remove(item)
                    print(f"Removed file: {item}")
                except OSError as e:
                    print(f"Error removing file {item}: {e}")
        print('All non-Python files cleared')
    except OSError as e:
        print(f"Error: {e}")

def list_files(client):
    files = []
    for item in uos.listdir():
        if uos.stat(item)[0] & 0x4000:  # Check if it's a directory
            for file in uos.listdir(item):
                files.append(f"{item}/{file}")
        else:
            files.append(item)
    client.send('\n'.join(files).encode())
    client.close()
    print('File list sent')

def send_file_to_client(client, file_name):
    try:
        with open(file_name, 'rb') as f:
            while True:
                chunk = f.read(1024)
                if not chunk:
                    break
                client.send(chunk)
        client.close()
        print(f'File {file_name} sent to client')
    except OSError as e:
        print(f"Error sending file {file_name}: {e}")

# Connect to Wi-Fi with the specified credentials
connect_wifi(ssid, password)
#connect_wifi('stewartnet', 'trawet07')
start_server()
  