""" This program runs on a ESP32 connected
    via serial link to the CNC machine
    
    Next upgrade is setup messaging back to client:
    1. Send connection status and info - Complete
    2. Send message confirming command receipt - Complete
    3. Revise receive_from_serial function to timeout if no data received after X attempts
    4. Set UART parameters comm parameters to match CNC machine selected and sent from client
      5. Change the flow control method to be used depending on the machine selected by the client

Changed the send_to_serial function prepend the XON character to the file data before sending it to the CNC machine.

"""

import network
import socket
import time
from machine import UART, reset 
import uos

ssid='StewartNet'
#ssid='stewartnet'
password='trawet07'

def send_status_message(client, message):
    try:
        client.sendall(f'Server Msg: {message}'.encode())
    except OSError as e:
        print(f"Error sending status message: {e}")


def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    # Set static IP address
    ip = '192.168.1.120'
    subnet = '255.255.255.0'
    gateway = '192.168.1.1'
    dns = '8.8.8.8'
    wlan.ifconfig((ip, subnet, gateway, dns))
    wlan.connect(ssid, password)
    
    while not wlan.isconnected():
        print('Connecting to network...')
        #send_status_message(cl,'Connecting to network...')
        time.sleep(1)
    
    print('Network connected!')
    print('IP address:', wlan.ifconfig()[0])
    #send_status_message(client,'Network conneted!')
    #send_status_message(cl,'IP address' + wlan.ifconfig()[0])


    
def start_server():
    addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reuse the address
    s.bind(addr)
    s.listen(1)
    #send_status_message(cl, "Connected!")
    #s.settimeout(30)  # Increase the timeout period to 30 seconds
    print('Listening on', addr)
    while True:
        #cl, addr = s.accept()
        time.sleep(.1)
        #send_status_message(cl, "Connected!")
        try:
            cl, addr = s.accept()
            print('Client connected from', addr)           
            data = cl.recv(1024)
            if data == b'CLEAR_FILES': #clears all files on ESP32, confirmed
                print("clearing files")
                clear_files()
                send_status_message(cl, 'All User files cleared on ESP32')
            elif data == b'LIST_FILES': #Lists all files on CNC - used after every op to refresh client list
                print("lists files")
                list_files(cl)
                send_status_message(cl, 'File list sent to client')
            elif data.startswith(b'SEND_FILE'): #Sends selected file to CNC
                print("Sending file to CNC serial port")
                file_name = data[len('SEND_FILE '):].decode()
                send_to_serial(file_name)
                send_status_message(cl, f'File {file_name} sent to CNC')
            elif data.startswith(b'DELETE_FILE'): #Deletes file selected on client window
                print("Deleted file: " + file_name)
                file_name = data[len('DELETE_FILE '):].decode()
                delete_file(file_name)
                send_status_message(cl, f'File {file_name} deleted from ESP32')

            elif data.startswith(b'RECEIVE_FILE'): # I think this gets a serial file from CNC
                print("Sending " + file_name + " to CNC")
                file_name = data[len('RECEIVE_FILE '):].decode()
                send_file_to_client(cl, file_name)
                send_status_message(cl, f'File {file_name} sent to client')

            elif data == b'REBOOT':
                send_status_message(cl, 'Reboot command received, \n            see you on the other side!')
                cl.close()
                print('Reboot command received')
                time.sleep(1)
                reset()  # Reboot the ESP32
            elif data == b'RECEIVE_SERIAL':
                receive_from_serial('serial_data.txt')  # Save serial data to 'serial_data.txt'
                send_status_message(cl, 'Serial data received and saved as serial_data.txt')
            #else: # this section sends selected file to PC
                print("else statement")
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

def handle_client_connection(client_socket):
    request = client_socket.recv(1024).decode()
    if request.startswith("SETUP_UART"):
        baudrate, parity, stopbits = request.split()
        baudrate = int(baudrate)
        stopbits = int(stopbits)
        uart_setup(baudrate, parity, stopbits)
        client_socket.send("UART setup complete".encode())
    else:
        # Handle other requests
        pass

def uart_setup(baudrate, parity, stopbits):
    parity_map = {'N': None, 'E': UART.EVEN, 'O': UART.ODD}
    uart = UART(1, baudrate=baudrate, parity=parity_map[parity], stop=stopbits)
    print(f"UART configured: baudrate={baudrate}, parity={parity}, stopbits={stopbits}")
    return uart

"""
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


"""
def send_to_serial(file_name): #with xon/xoff
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


def receive_from_serial(file_name):
    #time.sleep(0)
    uart = UART(1, baudrate=9600,tx=16, rx=17)  # Adjust pins and baudrate as needed
    #print("just before try loop")
    try:
        #print("inside try loop")
        #print(file_name)
        count=1
        with open(file_name, 'wb') as f:
            while True:
                count+=1
                print("inside True loop",count)
                chunk = uart.read(1024)
                time.sleep(1)
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
    #client.close()
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
