""" This program runs on a ESP32 connected
    via serial link to the CNC machine
    
    Next upgrade is setup messaging back to client:
    1. Send connection status and info - Complete
    2. Send message confirming command receipt - Complete
    3. Revise receive_from_serial function to timeout if no data received after X attempts - Complete
    4. Set UART parameters comm parameters to match CNC machine selected and sent from client - Complete, tested
    5. Change the flow control method to be used depending on the machine selected by the client
        Changed the send_to_serial function prepend the XON character to the file data before sending it to the CNC machine.
    6. Added timeout to receive_from_serial function to prevent infinite loop if no data is received - Complete
       Duration of loop is 200000 loops so about 20 seconds, maybe
    7. Implement xon/xoff software flow control - Complete but not tested at shop
    8. Added ability to try a second SSID if the first one fails - Complete
    9. Add a function to clear all files on the ESP32 - Complete
    10. Add a function to list all files on the ESP32 - Complete
    11. Add a function to delete a specified file on the ESP32 - Complete
    12. Add a function to send a specified file to the client - Complete
    13. Add a function to receive a file from the client - Complete
    14. Add a function to reboot the ESP32 - Complete
    15. Add a function to send a file to the CNC machine with software flow control - Complete
    16. Add a function to send a file to the CNC machine with hardware flow control - Complete
    17. Add a function to receive data from the CNC machine with software flow control - Complete
    18. Add a function to receive data from the CNC machine with hardware flow control - Complete
    19. Adding any necessary changes to work with html and flask - None needed yet
"""

import network
import socket
import time
from machine import UART, reset 
import uos
import urequests  # Add this import

ssid1 = "San Pietro all’Orto 6-P.2"
password1 = 'wearehappy'
ssid2 = 'StewartNet'
password2 = 'trawet07'

xonxoff = False
print("initial value of xonxoff:")
print(xonxoff)

# default UART configuration (Enshu)
uart = UART(1, baudrate=9600, bits=7, parity=1, stop=2, tx=16, rx=17, cts=18, rts=19) # remove timeout=1000

"""ssid='StewartNet'
#ssid='stewartnet'
password='trawet07'
uart = None"""
def send_status_message(client, message):
    try:
        client.sendall(f'Server Msg: {message}'.encode())
        # Send message to app.py
        url = 'http://192.168.1.109:5000/receive_message'  # Replace <app_ip> with the actual IP address of the machine running app.py
        payload = {'message': message}
        response = urequests.post(url, json=payload)
        response.close()
    except OSError as e:
        print(f"Error sending message: {e}")
        print(f"Error sending status message: {e}")


def connect_wifi(ssid1, password1, ssid2, password2):
    wlan = network.WLAN(network.STA_IF)
    #wlan.disconnect()
    wlan.active(False)
    wlan.active(True)
    # Set static IP address
    #ip = '192.168.1.120'
    #subnet = '255.255.255.0'
    #gateway = '192.168.1.1'
    #dns = '8.8.8.8'
    #wlan.ifconfig((ip, subnet, gateway, dns))

    def try_connect(ssid, password):
        #wlan.disconnect()
        print("inside try_connect")
        print(f"Trying to connect to network {ssid}...")
        if not wlan.isconnected():
            try:
                print("before wlan")
                if not wlan.isconnected():
                    print("Not connected to a network.")
                    wlan.connect(ssid, password)
                else:
                    print("Already connected to a network.")
                #wlan.connect(ssid, password)
                print("after wlan")
                if wlan.isconnected():
                    print(f'Connected to network {ssid}')
                    return True
                start_time = time.time()
                while not wlan.isconnected():
                    if time.time() - start_time > 10:
                        return False
                    print(f'Connecting to network {ssid}...')
                    time.sleep(1)
                return True
            except OSError as e:
                print(f"OSError - Error connecting to network {ssid}: {e}")
                return False
        else:
            print(f'Already connected to network {ssid}')
            return True

    # Try to connect to the first SSID
    if try_connect(ssid1, password1):
        print(f'Connected to {ssid1}')
    else:
        print(f'Failed to connect to {ssid1}, trying {ssid2}')
        # Try to connect to the second SSID
        if try_connect(ssid2, password2):
            print(f'Connected to {ssid2}')
        else:
            print(f'Failed to connect to {ssid2}')
            # Optionally, you can reset the device or handle the failure as needed
            print('Failed to connect to any network, resetting...')
            #reset()
    #send_status_message(client,'Network conneted!')
    #send_status_message(cl,'IP address' + wlan.ifconfig()[0])


    
def start_server():
    addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]
    s = socket.socket()
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reuse the address
        s.bind(addr)
        s.listen(1)  # This line specifies the maximum number of queued connections
        print('Listening on', addr)
        while True:
            time.sleep(.1)
            try:
                cl, addr = s.accept()  # Accepting client connections here
                print('Client connected from', addr)
                data = cl.recv(1024)
                
                if data == b'CLEAR_FILES':
                    print("clearing files")
                    clear_files()
                    send_status_message(cl, 'All User files cleared on ESP32')
                
                elif data == b'LIST_FILES':
                    print("lists files")
                    list_files(cl)
                    send_status_message(cl, 'File list sent to client')
                
                elif data.startswith(b'SEND_FILE'):
                    print("Sending file to CNC serial port")
                    file_name = data[len('SEND_FILE '):].decode()
                    global xonxoff
                    print("xonxoff value in server switch")
                    print(xonxoff)
                    if xonxoff == True:
                        send_to_serial_xonxoff(file_name)
                    else: send_to_serial(file_name)
                    send_status_message(cl, f'File {file_name} sent to CNC')
                
                elif data.startswith(b'DELETE_FILE'):
                    print("Deleted file: " + file_name)
                    file_name = data[len('DELETE_FILE '):].decode()
                    delete_file(file_name)
                    send_status_message(cl, f'File {file_name} deleted from ESP32')

                elif data.startswith(b'RECEIVE_FILE'):
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
                        print(f"Received data: {data}")
                        parts = data[len('SETUP_UART '):].decode().split()
                        print(f"Parts after splitting: {parts}")
                        print(f"Number of parts: {len(parts)}")
                        if len(parts) < 6:
                            raise ValueError("Invalid number of parameters for SETUP_UART")
                        
                        port = int(parts[0])  # Assuming port is an integer
                        baudrate = int(parts[1])
                        parity = parts[2]  # Assuming parity is not an integer
                        databits = int(parts[3])
                        stopbits = int(parts[4])
                        flowcontrol = ' '.join(parts[5:])  # Join the remaining parts into a single string
                        print(port, baudrate, parity, databits, stopbits, flowcontrol)
                        if 'xonxoff' in flowcontrol:
                            xonxoff = True
                        else:
                            xonxoff=False
                        print("xonxoff value in setup uart")
                        print(xonxoff)

                        # Define parity values directly
                        parity_map = {'N': 0, 'E': 1, 'O': 2}  # Assuming 0=None, 1=Even, 2=Odd
                        if parity not in parity_map:
                            raise ValueError(f"Invalid parity value: {parity}")
                        
                        uart_setup(port, baudrate, parity, databits, stopbits, flowcontrol)
                        print(baudrate)
                        uart_status = (f'\nCNC serial comms configured to: \nbaudrate={baudrate}\nparity={parity}\ndatabits={databits}\nstopbits={stopbits}\nflow={flowcontrol}\nport={port}\n')
                        send_status_message(cl, uart_status)
                        print("Status message sent")
                    except ValueError as e:
                        print(f"Error in UART setup: {e}")
                        send_status_message(cl, f"UART setup failed: {e}")

                else:
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
                    print(f"start_server generic OSError - Error: {e}")
            finally:
                cl.close()  # Ensure the client connection is closed. This is important! Otherwise, the server will hang als 
    finally:
        s.close()

def uart_setup(port, baudrate, parity, databits, stopbits, flowcontrol):
    global uart
    print("xonxoff value in uart_setup")
    print(xonxoff)
    # Map flow control strings to UART constants
    flowcontrol_map = {
        'None': 0,
        'UART.RTS': UART.RTS,
        'UART.CTS': UART.CTS,
        'UART.RTS | UART.CTS': UART.RTS | UART.CTS,
        'xonxoff': 0  # 0x100 is the constant for software flow control
    }
    print(parity)
    # Map parity strings to UART constants
    parity_map = {'None': None, '0': 0, '1': 1}

    # Validate flow control
    if flowcontrol not in flowcontrol_map:
        raise ValueError(f"Invalid flow control value: {flowcontrol}")

    # Validate parity
    #if parity not in parity_map:
        #raise ValueError(f"Invalid parity value: {parity}")
 
    # Print the parameters for debugging
    print(f" Settings going int uart def - port: {port}, baudrate: {baudrate}, parity: {parity}, databits: {databits},stopbits: {stopbits}, flowcontrol: {flowcontrol}")

    # Initialize UART with the mapped parameters
    
    #uart=UART(1,tx=16,rx=17,cts=18)

    uart = UART(
        1,
        baudrate=baudrate,
        bits=databits,
        #parity=parity_map[parity],
        parity=0,
        stop=stopbits,
        flow=flowcontrol_map[flowcontrol],
        tx=16,
        rx=17,
        cts=18,
        rts=19
    )

    # Print the configured UART for debugging
    #print(f"UART configured: port={port}, baudrate={baudrate}, parity={parity}, databits={databits}, stopbits={stopbits}, flow={flowcontrol}")
    print(f"UART configured: {port}, baudrate={baudrate}, parity={parity}, databits={databits}, stopbits={stopbits}, flow={flowcontrol}")

    return uart

def send_to_serial(file_name, timeout=10):  # Timeout in seconds
    print("Executing the send_to_serial function")
    global uart
    if uart is None:
        print("UART is not configured. Please call uart_setup first.")
        return
    print("Start time about to be called")

    start_time = time.time()  # Record the start time
    print("Start time:", start_time)

    try:
        with open(file_name, 'rb') as file:
            while True:
                # Check if timeout has been exceeded
                elapsed_time = time.time() - start_time
                print(time.time(), start_time)
                print("Elapsed time:", elapsed_time)
                if elapsed_time > timeout:
                    #time.sleep(.01)
                    print("send_to_serial - Timeout exceeded")
                    break

                # Read a chunk of the file
                chunk = file.read(1024)
                print(chunk)
                #print('\n')
                if not chunk:
                    print("past timeout check")
                    break

                # Send the chunk to the serial port
                uart.write(chunk)
                print("Sent chunk of size:", len(chunk))
    except Exception as e:
        print("send_to_serial - Error:", e)


def send_to_serial_xonxoff(file_name, timeout=10):  # Timeout in seconds
    print("Executing the send_to_serial_xonxoff function")
    global uart  # may need to adjust this for software flow control
    if uart is None:
        print("UART is not configured. Please call uart_setup first.")
        return
    XON = 0x11
    XOFF = 0x13
    flow_control = True
    print("calling time function")

    start_time = time.time()  # Record the start time

    try:
        print(time.time()-start_time)
        with open(file_name, 'rb') as f:
            # Prepend the XON character
            uart.write(bytes([XON])) # Send the XON character to the CNC machine as hex
        while True:
            chunk = f.read(1024)  # Read a chunk of the file
            if not chunk:
                break
            for char in chunk:
                while not flow_control:
                    print(time.time() - start_time)
                    if uart.any():
                        control_char = uart.read(1)
                        if control_char == bytes([XOFF]):
                            flow_control = False
                        elif control_char == bytes([XON]):
                            flow_control = True
                    # Check for timeout
                    if time.time() - start_time > timeout:
                        print("Timeout: Receiver did not respond in time.")
                        return
                    print(time.time() - start_time)
                    time.sleep(0.01)  # Small delay to prevent busy waiting
                uart.write(char.encode())  # Write the rest of the file to the UART in ascii
                print(f"Sent char: {char}")
                print(f'File {file_name} sent to serial device')
    except OSError as e:
        print(f"Error sending file {file_name}: {e}")


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
        print(f"clear_files - Error: {e}")

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
connect_wifi(ssid1, password1, ssid2, password2)
start_server()
