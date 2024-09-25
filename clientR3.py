"""
Revision 1 to Main Branch
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

# Constants
HOST = '192.168.1.120'
PORT = 8080

def show_message():
    messagebox.showinfo("Info", "This is a menu item")

def run_receiver():
    file_name = file_combobox.get()
    if file_name:
        save_path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=file_name)
        if save_path:
            receive_file(file_name, save_path)
    else:
        print("No file selected")

def receive_file(file_name, save_path):
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
        s.close()
        print(f'File {file_name} received and saved to {save_path}')
    except socket.error as e:
        print(f"Socket error: {e}")

def send_file(file_path, host, port):
    file_name = os.path.basename(file_path)
    with open(file_path, 'rb') as f:
        data = f.read()
    
    try:
        s = socket.socket()
        s.connect((host, port))
        s.sendall(file_name.encode() + b'\n' + data)
        s.close()
        print('File sent')
        update_file_list()  # Refresh the file list after sending a file
    except socket.error as e:
        print(f"Socket error: {e}")

def select_and_send_file():
    file_path = filedialog.askopenfilename(title="Select a file to send")
    if file_path:
        send_file(file_path, HOST, PORT)
    else:
        print("No file selected")

def clear_files_on_esp32():
    try:
        s = socket.socket()
        s.connect((HOST, PORT))
        s.sendall(b'CLEAR_FILES')
        s.close()
        print('Clear files command sent')
        update_file_list()  # Refresh the file list after clearing files
    except socket.error as e:
        print(f"Socket error: {e}")

def list_files_on_esp32():
    try:
        s = socket.socket()
        s.connect((HOST, PORT))
        s.sendall(b'LIST_FILES')
        data = s.recv(4096).decode()
        s.close()
        print('Files on ESP32:')
        print(data)
        return data.split('\n')
    except socket.error as e:
        print(f"Socket error: {e}")
        return []

def update_file_list():
    files = list_files_on_esp32()
    file_combobox['values'] = files
    if files:
        file_combobox.current(0)

def send_selected_file():
    file_name = file_combobox.get()
    if file_name:
        try:
            s = socket.socket()
            s.connect((HOST, PORT))
            s.sendall(f'SEND_FILE {file_name}'.encode())
            s.close()
            print(f'Send file command for {file_name} sent')
            update_file_list()  # Refresh the file list after sending a file
        except socket.error as e:
            print(f"Socket error: {e}")
    else:
        print("No file selected")

def delete_selected_file():
    file_name = file_combobox.get()
    if file_name:
        try:
            s = socket.socket()
            s.connect((HOST, PORT))
            s.sendall(f'DELETE_FILE {file_name}'.encode())
            s.close()
            print(f'Delete file command for {file_name} sent')
            update_file_list()  # Refresh the file list after deleting a file
        except socket.error as e:
            print(f"Socket error: {e}")
    else:
        print("No file selected")

def send_reboot_command():
    try:
        s = socket.socket()
        s.connect((HOST, PORT))
        s.sendall(b'REBOOT')
        s.close()
        print('Reboot command sent')
    except socket.error as e:
        print(f"Socket error: {e}")

# Create the main window
root = tk.Tk()
root.title("Send_V9 GUI")

# Load the image using PIL
pil_image = Image.open("C:/Users/stewa/Documents/StewartMachine/Industrial Automation/SMLogo.png")
image = ImageTk.PhotoImage(pil_image)

# Create a label to display the image
image_label = tk.Label(root, image=image)
image_label.grid(row=0, column=0, columnspan=2)

# Add buttons and other GUI components
send_button = tk.Button(root, text="Upload New File to ESP32", command=select_and_send_file)
send_button.grid(row=1, column=0, padx=10, pady=10)

receive_button = tk.Button(root, text="Receive File", command=run_receiver)
receive_button.grid(row=1, column=1, padx=10, pady=10)

delete_button = tk.Button(root, text="Delete Selected File", command=delete_selected_file)
delete_button.grid(row=2, column=0, padx=10, pady=10)

clear_button = tk.Button(root, text="Clear Files on ESP32", command=clear_files_on_esp32)
clear_button.grid(row=2, column=1, padx=10, pady=10)

send_selected_button = tk.Button(root, text="Send Selected File to CNC", command=send_selected_file)
send_selected_button.grid(row=3, column=0, padx=10, pady=10)

reboot_button = tk.Button(root, text="Restart ESP32", command=send_reboot_command)
reboot_button.grid(row=3, column=1, padx=10, pady=10)

# Add a combobox for selecting files
file_combobox = ttk.Combobox(root)
file_combobox.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

# Initial update of the file list
update_file_list()

# Run the application
root.mainloop()