"""
User Interface GUI
This code generates the user interface and provides
basic functionality such as:
Send to remote interface (ESP32)
Receive file listing from remote interface
Commands to serially transmit selected files to CNC machine connected to remote interface.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import socket
import os

# Constants
HOST = '192.168.1.120'
PORT = 8080

def show_message():
    """Display an informational message box."""
    messagebox.showinfo("Info", "This is a menu item")

def run_receiver():
    """Prompt user to select a file and save path, then receive the file from the remote interface."""
    file_name = file_combobox.get()
    if file_name:
        save_path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=file_name)
        if save_path:
            receive_file(file_name, save_path)
    else:
        print("No file selected")

def receive_file(file_name, save_path):
    """Receive a file from the remote interface and save it to the specified path."""
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

def send_reboot_command():
    try:
        s = socket.socket()
        s.connect((HOST, PORT))
        s.sendall(b'REBOOT')
        s.close()
        print('Reboot command sent')
    except socket.error as e:
        print(f"Socket error: {e}")

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

# Create the main window
root = tk.Tk()
root.title("Stewart Machine - 2024")

# Create a blue banner
banner = tk.Frame(root, bg="blue", height=50)
banner.pack(fill="x")

banner_label1 = tk.Label(banner, text="Stewart Machine", bg="blue", fg="white", font=("Helvetica", 24))
banner_label1.pack()
banner_label2 = tk.Label(banner, text="Industrial Automation Division", bg="blue", fg="white", font=("Courier", 16))
banner_label2.pack()

# Create a menu bar
menu_bar = tk.Menu(root)

# Create a File menu
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Open", command=show_message)
file_menu.add_command(label="Save", command=show_message)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)
menu_bar.add_cascade(label="File", menu=file_menu)

# Create an Edit menu
edit_menu = tk.Menu(menu_bar, tearoff=0)
edit_menu.add_command(label="Cut", command=show_message)
edit_menu.add_command(label="Copy", command=show_message)
edit_menu.add_command(label="Paste", command=show_message)
menu_bar.add_cascade(label="Edit", menu=edit_menu)

# Add the menu bar to the window
# root.config(menu=menu_bar)

# Add buttons to the window
receive_button = tk.Button(root, text="Download from ESP32", command=run_receiver)
receive_button.pack(padx=100,pady=10)

send_button = tk.Button(root, text="Upload New File to ESP32", command=select_and_send_file)
send_button.pack(pady=10)

list_button = tk.Button(root, text="Refresh ESP32 File List", command=update_file_list)
list_button.pack(pady=10)

clear_button = tk.Button(root, text="Delete All Files", command=clear_files_on_esp32)
clear_button.pack(pady=10)

# Add a separator
separator = ttk.Separator(root, orient='horizontal')
separator.pack(fill='x', pady=10)

# Add a title above the combobox
file_label = tk.Label(root, text="Select File to Send to CNC or Delete from ESP32")
file_label.pack(pady=10)

# Add a combobox for selecting files
file_combobox = ttk.Combobox(root)
file_combobox.pack(pady=10)

send_selected_button = tk.Button(root, text="Send Selected File to CNC", command=send_selected_file)
send_selected_button.pack(pady=10)

delete_selected_button = tk.Button(root, text="Delete Selected File", command=delete_selected_file)
delete_selected_button.pack(pady=10)

reboot_button = tk.Button(root, text="Restart ESP32", command=send_reboot_command)
reboot_button.pack(pady=10)

# Initial update of the file list
update_file_list()

# Run the application
root.mainloop()
