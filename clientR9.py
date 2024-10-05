"""
Revision 3 to Main Branch - ClientR7.py checks out good.
User Interface GUI
This code generates the user interface and provides
basic functionality such as:
Send to remote interface (ESP32)
Receive file listing from remote interface
Commands to serially transmit selected files to CNC machine connected to remote interface.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import socket
import os
import time

# Constants
HOST = '192.168.1.120'
PORT = 8080

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
        s = socket.socket()
        s.connect((HOST, PORT))
        s.sendall(b'REBOOT')
        update_status('Reboot command sent')
        status = s.recv(1024).decode()  # Wait for status message
        update_status(status) 
        s.close()
    except socket.error as e:
        update_status(f"Socket error: {e}")

def request_serial_data():
    try:
        s = socket.socket()
        s.connect((HOST, PORT))
        s.sendall(b'RECEIVE_SERIAL')
        s.close()
        update_status('Request to receive serial data sent')
        update_file_list()  # Refresh the file list
    except socket.error as e:
        update_status(f"Socket error: {e}")

def receive_file(file_name, save_path): # This function causes a selected file on ESP32 to be sent to the client
    try:
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
        update_status(f"Socket error: {e}")

def send_file(file_path, host, port):
    file_name = os.path.basename(file_path)
    with open(file_path, 'rb') as f:
        data = f.read()
    
    try:
        s = socket.socket()
        s.connect((host, port))
        s.sendall(file_name.encode() + b'\n' + data)
        update_status('File sent to ESP32: ' + file_name)
        #status = s.recv(1024).decode()  # Wait for status message
        #update_status(status)    
        s.close()
        update_file_list()  # Refresh the file list after sending a file
    except socket.error as e:
        update_status(f"Socket error: {e}")

def select_and_send_file():
    file_path = filedialog.askopenfilename(title="Select a file to send")
    if file_path:
        send_file(file_path, HOST, PORT)
    else:
        update_status("No file selected")

def clear_files_on_esp32():
    try:
        s = socket.socket()
        s.connect((HOST, PORT))
        s.sendall(b'CLEAR_FILES')
        update_status("Command to files cleared on ESP32 sent")
        status = s.recv(1024).decode()  # Wait for status message
        s.close()
        update_status(status)
        update_file_list()  # Refresh the file list after clearing files
    except socket.error as e:
        update_status(f"Socket error: {e}")

def list_files_on_esp32():
    try:
        s = socket.socket()
        s.connect((HOST, PORT))
        s.sendall(b'LIST_FILES')
        data = s.recv(4096).decode()
        s.close()
        #update_status('Files on ESP32:')
        #update_status(data)
        return data.split('\n')
    except socket.error as e:
        #update_status(f"Socket error: {e}\n"+ "Server Device Not Found\n" + "Verify ESP32 Powered\nIf ESP32 was powered, wait 1m\nwhile it acquires IP Address from router\nand try again\n")
        update_status(f"Socket error:\n"+ "Server Device Not Found\n" + "Verify ESP32 Powered\nIf ESP32 was powered, wait 1m\nwhile it acquires IP Address from router\nand try again\n")

        return []

def send_selected_file_serial(): #Command to send selected file to CNC machine without flow control
    file_name = file_combobox.get()
    if file_name:
        try:
            s = socket.socket()
            s.connect((HOST, PORT))
            s.sendall(f'SEND_FILE_SERIAL {file_name}'.encode())
            status = s.recv(1024).decode()  # Wait for status message
            time.sleep(.1)
            s.close()
            update_status(status)
            update_file_list()  # Refresh the file list after sending a file
        except socket.error as e:
            update_status(f"Socket error: {e}")
    else:
        update_status("No file selected")

def send_selected_file_serialFC(): #Command to send selected file to CNC machine without flow control
    file_name = file_combobox.get()
    if file_name:
        try:
            s = socket.socket()
            s.connect((HOST, PORT))
            s.sendall(f'FC_SEND_FILE_SERIAL {file_name}'.encode())
            print("debug message: " + file_name)
            status = s.recv(1024).decode()  # Wait for status message
            time.sleep(.1)
            s.close()
            update_status(status)
            update_file_list()  # Refresh the file list after sending a file
        except socket.error as e:
            update_status(f"Socket error: {e}")
    else:
        update_status("No file selected")

def delete_selected_file():
    file_name = file_combobox.get()
    if file_name:
        try:
            s = socket.socket()
            s.connect((HOST, PORT))
            s.sendall(f'DELETE_FILE {file_name}'.encode())
            status = s.recv(1024).decode()  # Wait for status message
            update_status(status)
            s.close()
            update_file_list()  # Refresh the file list after deleting a file
        except socket.error as e:
            update_status(f"Socket error: {e}")
    else:
        update_status("No file selected")

def show_message():
    messagebox.showinfo("Info", "This is a menu item")

  
def update_file_list():
    files = list_files_on_esp32()
    file_combobox['values'] = files
    if files:
        file_combobox.current(0)


# Create the main window
root = tk.Tk()
root.title("Graphic User Interface for Stewart Machine")

# Load the image using PIL and scale it by half
# since this image is hard coded to my home computer the program crashes
# if I run it from another location, need to address


#pil_image = Image.open("C:/Users/stewa/Pictures/SMLogo.png")
pil_image = Image.open("C:/Users/stewa/Documents/StewartMachine/Industrial Automation/SMLogo.png")
width, height = pil_image.size
scaled_image = pil_image.resize((width // 3, height // 3), Image.LANCZOS)
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

send_selected_button = tk.Button(root, text="Send Selected File to CNC without Flow Control", command=send_selected_file_serial)
send_selected_button.grid(row=3, column=1, padx=10, pady=10)

send_selected_button = tk.Button(root, text="Send Selected File to CNC Using Flow Control", command=send_selected_file_serialFC)
send_selected_button.grid(row=4, column=1, padx=10, pady=10)

reboot_button = tk.Button(root, text="Restart ESP32", command=send_reboot_command)
reboot_button.grid(row=4, column=0, padx=10, pady=10)

# Add a combobox for selecting files
file_combobox = ttk.Combobox(root)
file_combobox.grid(row=5, column=1, padx=10, pady=10)

# Add a status box
status_text = tk.Text(root, height=10, width=50)
status_text.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

def update_status(message):
    #status_text.insert(tk.END, "update status loop entered" + '\n')
    status_text.insert(tk.END, message + '\n')
    status_text.see(tk.END)



# Initial update of the file list
update_file_list()

# Run the application
root.mainloop()