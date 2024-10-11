""" This program runs on a ESP32 connected
    via serial link to the CNC machine
    
    Next upgrade is setup messaging back to client:
    1. Send connection status and info - Complete
    2. Send message confirming command receipt - Complete
    3. Revise receive_from_serial function to timeout if no data received after X attempts
    4. Set UART parameters comm parameters to match CNC machine selected and sent from client - Complete, tested
    5. Change the flow control method to be used depending on the machine selected by the client
        Changed the send_to_serial function prepend the XON character to the file data before sending it to the CNC machine.
    6. Added timeout to receive_from_serial function to prevent infinite loop if no data is received - Complete
       Duration of loop is 200000 loops so about 20 seconds, maybe

"""

import network
import socket
import time
from machine import UART, reset 
import uos

ssid='StewartNet'
#ssid='stewartnet'
password='trawet07'
uart = None

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
        send_status_message(cl, "Connected!")
         
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

            elif data.startswith(b'SETUP_UART'):
                try:
                    parts = data[len('SETUP_UART '):].decode().split()
                    if len(parts) != 6:
                        raise ValueError("Invalid number of parameters for SETUP_UART")
                    
                    baudrate, parity, stopbits, databits, flowcontrol, port = parts
                    baudrate = int(baudrate)
                    stopbits = int(stopbits)
                    databits = int(databits)
                    flowcontrol = (flowcontrol)  # Assuming flowcontrol is not an integer
                    port = int(port)  # Assuming port is an integer
                    
                    # Define parity values directly
                    parity_map = {'N': 0, 'E': 1, 'O': 2}  # Assuming 0=None, 1=Even, 2=Odd
                    if parity not in parity_map:
                        raise ValueError(f"Invalid parity value: {parity}")
                    
                    uart_setup(baudrate, parity_map[parity], stopbits, databits, flowcontrol, port)
                    print(baudrate)
                    uart_status = (f'\nCNC serial comms configured to: \nbaudrate={baudrate}\nparity={parity}\nstopbits={stopbits}\ndatabits={databits}\nflow={flowcontrol}\nport={port}\n')
                    send_status_message(cl, uart_status)
                    print("Status message sent")
                except ValueError as e:
                    print(f"Error in UART setup: {e}")
                    send_status_message(cl, f"UART setup failed: {e}")

            else: # this section sends selected file to PC
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

"""
def handle_client_connection(client_socket):
    request = client_socket.recv(1024).decode()
    print("Received request:", request)
    if request.startswith("SETUP_UART"):
        baudrate, parity, stopbits = request.split()
        baudrate = int(baudrate)
        stopbits = int(stopbits)
        uart_setup(baudrate, parity, stopbits)
        client_socket.send("UART setup complete".encode())
    else:
        # Handle other requests
        pass
"""

"""
### Plan
1. List all possible parameters for the `UART` class in MicroPython.
2. Provide a brief description of each parameter.

### Parameters for `UART` in MicroPython
- `id`: UART bus ID (e.g., 0, 1, etc.).
- `baudrate`: Communication speed in bits per second.
- `bits`: Number of data bits (typically 8).
- `parity`: Parity checking (None, 0 for even, 1 for odd).
- `stop`: Number of stop bits (1 or 2).
- `tx`: TX pin number.
- `rx`: RX pin number.
- `rts`: RTS pin number (optional, for hardware flow control).
- `cts`: CTS pin number (optional, for hardware flow control).
- `flow`: Flow control (None, `UART.RTS`, `UART.CTS`, `UART.RTS | UART.CTS`, `UART.XON_XOFF`).

Example Code
```python
from machine import UART

# Initialize UART with all possible parameters
uart = UART(
    id=1,                # UART bus ID
    baudrate=9600,       # Baud rate
    bits=8,              # Data bits
    parity=None,         # Parity (None, 0 for even, 1 for odd)
    stop=1,              # Stop bits
    tx=17,               # TX pin
    rx=16,               # RX pin
    rts=None,            # RTS pin (optional)
    cts=None,            # CTS pin (optional)
    flow=UART.XON_XOFF   # Flow control (None, UART.RTS, UART.CTS, UART.RTS | UART.CTS, UART.XON_XOFF)
)

def send_data(data):
    uart.write(data)

# Example usage
send_data("Hello, UART with all parameters!")
```

Explanation
- `id`: Specifies which UART bus to use.
- `baudrate`: Sets the speed of communication.
- `bits`: Defines the number of data bits per character.
- `parity`: Configures parity checking.
- `stop`: Sets the number of stop bits.
- `tx` and `rx`: Define the pins used for transmission and reception.
- `rts` and `cts`: Optional pins for hardware flow control.
- `flow`: Configures flow control method.
"""

def uart_setup(baudrate, parity, stopbits, databits, flowcontrol, port):
    print(baudrate, parity, stopbits, databits)
    global uart
    #print("Setting up UART")
    #parity_map = {'N': None, 'E': 0, 'O': 1}
    print(baudrate, parity, stopbits, databits, flowcontrol, port)
    
    uart = UART(port=port,baudrate=9600,bits=8,parity=None,stop=1,tx=16,rx=17,cts=18, rts=19, txbuf=256,rxbuf=256)
    #uart = UART(1, baudrate=baudrate, parity=parity_map[parity], stop=stopbits, tx=16, rx=17)
    print(f"UART configured: baudrate={baudrate}, parity={parity}, databits={databits}, stopbits={stopbits}")
    return uart

"""
def send_to_serial(file_name): #no xon/xoff
    global uart
    #uart = UART(1, baudrate=9600, tx=16, rx=17, bits=8, parity=None, stop=1)  # Adjust pins and baudrate as needed

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
def send_to_serial(file_name):
    # Open the serial port with xon/xoff flow control
    global uart
    #uart = machine.UART(serial_port, baudrate=9600, flow=machine.UART.XON_XOFF)
    
    try:
        # Open the file in binary read mode
        with open(file_name, 'rb') as file:
            while True:
                # Read a chunk of the file
                chunk = file.read(1024)
                if not chunk:
                    break
                # Send the chunk to the serial port
                UART.write(chunk)
    except Exception as e:
        print("Error:", e)
    #finally:
        # Close the serial port
        #uart.deinit()

'''
def send_to_serial(file_name): #with xon/xoff <--- this is the one that works
    print("Executing the send_to_serial function")
    global uart
    if uart is None:
        print("UART is not configured. Please call uart_setup first.")
        return
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
'''

def receive_from_serial(file_name):
    global uart
    #time.sleep(0)
    #uart = UART(1, baudrate=9600,tx=16, rx=17)  # Adjust pins and baudrate as needed
    #print("just before try loop")
    try:
        #print("inside try loop")
        #print(file_name)
        count=1
        with open(file_name, 'wb') as f:
            while True:
                count+=1
                #print("inside while loop: ",2000-count)
                chunk = uart.read(1024)
                #time.sleep(1)
                #print(chunk)
                if count>=200000:
                    print("No Data from Serial Port, exiting")
                    break
                if chunk:
                    f.write(chunk)
                    print(chunk)
                    #time.sleep(.1)
                    #if (b'%' or b'M30') in chunk:
                    #print(20-count, "timeout counter")
                    if ('M30') in chunk:
                      break

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
