"""
Partially tested code for Revision 10.  No known issues at this time.

Revision 10 branch began with known good Revision 7.
User Interface GUI
This code generates the user interface and provides
basic functionality such as:
Send to remote interface (ESP32)
Receive file listing from remote interface
Commands to serially transmit selected files to CNC machine connected to remote interface.

Modifications planned for Revision 10:
1. Change the way the HOST and PORT values are set depending on the machine selected. - Complete, partially tested
2. Send the method of flow control to be used ESP32 depending on the machine selected. - Not started
   a. Will need a way to set the flow control method on the ESP32 side. - Not started
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import socket
import os
import time

# Define HOST and PORT constants
HOST = "192.168.1.120"  # Set default host to 192.168.1.120
PORT = 8080  # Set default port to 8080

# Dictionary to map machine names to their respective HOST and PORT values
machine_config = {
    'Enshu': {'HOST': '192.168.1.120', 'PORT': 8080},
    'Wyatt': {'HOST': '192.168.1.120', 'PORT': 8080},
    'Hyundai': {'HOST': '192.168.1.120', 'PORT': 8080},
    'Frenchy': {'HOST': '192.168.1.120', 'PORT': 8080}
}

# Debug print statement
print("machine_config:", machine_config)

"""
https://docs.micropython.org/en/latest/library/machine.UART.html
flow specifies which hardware flow control signals to use. The value is a bitmask.
-0 will ignore hardware flow control signals.
-UART.RTS will enable receive flow control by using the RTS output pin to signal if the receive FIFO has sufficient space to accept more data.
-UART.CTS will enable transmit flow control by pausing transmission when the CTS input pin signals that the receiver is running low on buffer space.
-UART.RTS | UART.CTS will enable both, for full hardware flow control.""" 

# UART flowcontrol options: 'UART.RTS | UART.CTS', 'UART.XON_XOFF', 'None'
uart_config = {
    'Enshu': {'baudrate': 9600, 'parity': 'E', 'databits': 7, 'stopbits': 2, 'flowcontrol': 'None', 'port': 1},
    'Wyatt': {'baudrate': 9600, 'parity': 'N', 'databits': 8, 'stopbits': 1,  'flowcontrol': 'None', 'port': 1},
    'Hyundai': {'baudrate': 9600, 'parity': 'N', 'databits': 8, 'stopbits': 1,  'flowcontrol': 'xonxoff', 'port': 1},
    'Frenchy': {'baudrate': 9600, 'parity': 'N', 'databits': 8, 'stopbits': 1,  'flowcontrol': 'UART.RTS | UART.CTS', 'port': 1}
}

# Modify existing functions to update the status box
def run_receiver():
    file_name = file_combobox.get()
    if file_name:
        save_path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=file_name)
        if save_path:
            receive_file(file_name, save_path)
    else:
        update_status("No file selected")

def send_reboot_command():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s = socket.socket()
            s.connect((HOST, PORT))
            s.sendall(b'REBOOT')
            update_status('Reboot command sent')
            status = s.recv(1024).decode()  # Wait for status message
            update_status(status) 
            s.close()
    except socket.error as e:
        update_status(f"send_reboot_command - Socket error: {e}")

def request_serial_data():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s = socket.socket()
            s.connect((HOST, PORT))
            s.sendall(b'RECEIVE_SERIAL')
            s.close()
            update_status('Request to receive serial data sent')
            update_file_list()  # Refresh the file list
    except socket.error as e:
        update_status(f"request_serial_data - Socket error: {e}")

def receive_file(file_name, save_path): # This function causes a selected file on ESP32 to be sent to the client
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s = socket.socket()
            s.connect((HOST, PORT))
            s.sendall(f'RECEIVE_FILE {file_name}'.encode())
            
            with open(save_path, 'wb') as f:
                while True:
                    data = s.recv(1024)
                    if not data:
                        break
                    f.write(data)
            
            status = s.recv(1024).decode()  # Wait for status message
            time.sleep(.1)
            update_status(f'File {file_name} received and saved to {save_path}')
            update_status(status) 
            s.close()
    except socket.error as e:
        update_status(f"receive_file - Socket error: {e}")

def send_file(file_path, host, port):
    file_name = os.path.basename(file_path)
    with open(file_path, 'rb') as f:
        data = f.read()
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s = socket.socket()
            s.connect((host, port))
            s.sendall(file_name.encode() + b'\n' + data)
            update_status('File sent to ESP32: ' + file_name)
            #status = s.recv(1024).decode()  # Wait for status message
            #update_status(status)    
            s.close()
            update_file_list()  # Refresh the file list after sending a file
    except socket.error as e:
        update_status(f"send_file - Socket error: {e}")

def select_and_send_file():
    file_path = filedialog.askopenfilename(title="Select a file to send")
    if file_path:
        send_file(file_path, HOST, PORT)
    else:
        update_status("No file selected")

def clear_files_on_esp32():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s = socket.socket()
            s.connect((HOST, int(PORT)))  # Ensure PORT is an integer
            s.sendall(b'CLEAR_FILES')
            update_status("Command to files cleared on ESP32 sent")
            status = s.recv(1024).decode()  # Wait for status message
            s.close()
            update_status(status)
            update_file_list()  # Refresh the file list after clearing files
    except socket.error as e:
        update_status(f"clear_files_on_esp32 - Socket error: {e}")

def list_files_on_esp32():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s = socket.socket()
            s.connect((HOST, int(PORT)))  # Ensure PORT is an integer
            s.sendall(b'LIST_FILES')
            data = s.recv(4096).decode()
            s.close()
            #update_status('Files on ESP32:')
            #update_status(data)
        return data.split('\n')
    except socket.error as e:
        #update_status(f"Socket error: {e}\n"+ "Server Device Not Found\n" + "Verify ESP32 Powered\nIf ESP32 was powered, wait 1m\nwhile it acquires IP Address from router\nand try again\n")
        update_status(f"list_files_on_esp32 - Socket error:\n"+ "Server Device Not Found\n" + "Verify ESP32 Powered\nIf ESP32 was powered, wait 1m\nwhile it acquires IP Address from router\nand try again\n")

        return []

def send_selected_file(): #Command to send selected file to CNC machine
    file_name = file_combobox.get()
    if file_name:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s = socket.socket()
                s.connect((HOST, int(PORT)))  # Ensure PORT is an integer
                s.sendall(f'SEND_FILE {file_name}'.encode())
                status = s.recv(1024).decode()  # Wait for status message
                s.close()
                update_status(status)
        except socket.error as e:
            update_status(f"send_selected_file - Socket error: {e}")
    else:
        update_status("No file selected")

def delete_selected_file():
    file_name = file_combobox.get()
    if file_name:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s = socket.socket()
                s.connect((HOST, PORT))
                s.sendall(f'DELETE_FILE {file_name}'.encode())
                status = s.recv(1024).decode()  # Wait for status message
                update_status(status)
                s.close()
                update_file_list()  # Refresh the file list after deleting a file
        except socket.error as e:
            update_status(f"delete_selected_file - Socket error: {e}")
    else:
        update_status("No file selected")

def show_message():
    messagebox.showinfo("Info", "This is a menu item")

  
def update_file_list():
    files = list_files_on_esp32()
    files.insert(0, "            Select File")
    file_combobox['values'] = files
    if files:
        file_combobox.current(0)


# Create the main window
root = tk.Tk()
root.title("Send_V9 GUI")

# Load the image using PIL and scale it by half
# since this image is hard coded to my home computer the program crashes
# if I run it from another location, need to address


#pil_image = Image.open("C:/Users/stewa/Pictures/SMLogo.png")
pil_image = Image.open("C:/Users/stewa/Documents/StewartMachine/Industrial Automation/SMLogo.png")
width, height = pil_image.size
scaled_image = pil_image.resize((width // 2, height // 2), Image.LANCZOS)
image = ImageTk.PhotoImage(scaled_image)


# Create a label to display the image
image_label = tk.Label(root, image=image)
image_label.grid(row=0, column=0, columnspan=2)

# Add buttons and other GUI components
send_button = tk.Button(root, text="Upload New File to ESP32", command=select_and_send_file)
send_button.grid(row=1, column=0, padx=10, pady=10)

receive_button = tk.Button(root, text="Receive Selected File from ESP32", command=run_receiver)
receive_button.grid(row=1, column=1, padx=10, pady=10)

serial_button = tk.Button(root, text="Receive Serial Data from CNC", command=request_serial_data)
serial_button.grid(row=2, column=0, padx=10, pady=10)

delete_button = tk.Button(root, text="Delete Selected File", command=delete_selected_file)
delete_button.grid(row=2, column=1, padx=10, pady=10)

clear_button = tk.Button(root, text="Clear Files on ESP32", command=clear_files_on_esp32)
clear_button.grid(row=3, column=0, padx=10, pady=10)

send_selected_button = tk.Button(root, text="Send Selected File to CNC", command=send_selected_file)
send_selected_button.grid(row=3, column=1, padx=10, pady=10)

reboot_button = tk.Button(root, text="Restart ESP32", command=send_reboot_command)
reboot_button.grid(row=4, column=0, padx=10, pady=10)

# Add a combobox for selecting files
file_combobox = ttk.Combobox(root)
file_combobox.grid(row=4, column=1, padx=10, pady=10)
file_combobox['values'] = ['            Select File']
file_combobox.current(0)

# Add a combobox to select machine from predefined list of machines
machine_combobox = ttk.Combobox(root)
machine_combobox.grid(row=5, column=1, padx=10, pady=10)
machine_combobox['values'] = ['        Select Machine', 'Enshu', 'Wyatt', 'Hyundai', 'Frenchy']
machine_combobox.current(0)

# Add a status box
status_text = tk.Text(root, height=10, width=50)
status_text.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

def update_status(message):
    status_text.insert(tk.END, message + '\n')
    status_text.see(tk.END)

def update_host_port(event=None):
    print("host port def")
    global HOST, PORT
    selected_machine = machine_combobox.get().strip()
    if selected_machine in machine_config:
        HOST = machine_config[selected_machine]['HOST']
        PORT = machine_config[selected_machine]['PORT']
        print(HOST, "this is host in update_host_port") #als debug
        try:
            PORT = int(machine_config[selected_machine]['PORT'])  # Convert PORT to integer
            HOST = machine_config[selected_machine]['HOST']
        except ValueError:
            update_status(f"Invalid PORT value for {selected_machine}. Using default port 12345.")
            PORT = 12345  # Default port value
            print("using port 12345")
        update_status(f"Updated HOST to {HOST} and PORT to {PORT} for {selected_machine}")

def send_uart_setup_details():
    selected_machine = machine_combobox.get().strip()
    if selected_machine in uart_config:
        uart_details = uart_config[selected_machine]
        message = (
            f"SETUP_UART {uart_details['port']} {uart_details['baudrate']} {uart_details['parity']} {uart_details['databits']} {uart_details['stopbits']} {uart_details['flowcontrol']} ")
            #f"SETUP_UART {uart_details['port']} {uart_details['baudrate']} {uart_details['parity']} {uart_details['databits']} {uart_details['stopbits']} ")
        print(message)
        send_message_to_server(message)

def send_message_to_server(message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            print("Message being sent to: ", HOST)
            print("Message being sent to: ", PORT)
            s.connect((HOST, int(PORT)))  # Ensure PORT is an integer
            s.sendall(message.encode())
            response = s.recv(1024).decode()
            update_status(f"{response}")
    except socket.error as e:
        update_status(f"send_message_to_server - Socket error: {e}")

# Initial update of the file list
update_file_list()

# Ensure HOST and PORT are updated before any socket connection attempts
update_host_port()

# Bind the update_host_port function to the <<ComboboxSelected>> event
machine_combobox.bind("<<ComboboxSelected>>", update_host_port)

# Bind the send_uart_setup_details function to the <<ComboboxSelected>> event
machine_combobox.bind("<<ComboboxSelected>>", lambda event: send_uart_setup_details())

# Run the application
root.mainloop()
