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

def select_and_send_file():
    file_path = filedialog.askopenfilename(title="Select a file to send")
    if file_path:
        send_file(file_path, HOST, PORT)
    else:
        print("No file selected")

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

def update_file_list():
    files = list_files_on_esp32()
    file_combobox['values'] = files
    if files:
        file_combobox.current(0)

def send_file(file_path, host, port):
    try:
        s = socket.socket()
        s.connect((host, port))
        s.sendall(f'SEND_FILE {os.path.basename(file_path)}'.encode())
        
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(1024)
                if not chunk:
                    break
                s.send(chunk)
        s.close()
        print(f'File {file_path} sent to ESP32')
        update_file_list()  # Refresh the file list after sending a file
    except socket.error as e:
        print(f"Socket error: {e}")

def send_reboot_command():
    try:
        s = socket.socket()
        s.connect((HOST, PORT))
        s.sendall(b'REBOOT')
        s.close()
        print('Reboot command sent to ESP32')
    except socket.error as e:
        print(f"Socket error: {e}")

# Create the main window
root = tk.Tk()
root.title("Send_V9 GUI")

# Load the image using PIL
pil_image = Image.open("C:/Users/stewa/Documents/StewartMachine/Industrial Automation/SMLogo.png")
image = ImageTk.PhotoImage(pil_image)

# Create a canvas to place the image and buttons
canvas = tk.Canvas(root, width=pil_image.width, height=pil_image.height)
canvas.pack()

# Add the image to the canvas
canvas.create_image(0, 0, anchor=tk.NW, image=image)

# Add buttons on top of the image
receive_button = tk.Button(root, text="Download from ESP32", command=run_receiver)
canvas.create_window(50, 50, anchor=tk.NW, window=receive_button)

send_button = tk.Button(root, text="Upload New File to ESP32", command=select_and_send_file)
canvas.create_window(50, 100, anchor=tk.NW, window=send_button)

list_button = tk.Button(root, text="Refresh ESP32 File List", command=update_file_list)
canvas.create_window(50, 150, anchor=tk.NW, window=list_button)

clear_button = tk.Button(root, text="Delete All Files", command=clear_files_on_esp32)
canvas.create_window(50, 200, anchor=tk.NW, window=clear_button)

send_selected_button = tk.Button(root, text="Send Selected File to CNC", command=send_selected_file)
canvas.create_window(50, 250, anchor=tk.NW, window=send_selected_button)

delete_selected_button = tk.Button(root, text="Delete Selected File", command=delete_selected_file)
canvas.create_window(50, 300, anchor=tk.NW, window=delete_selected_button)

# Add a combobox for selecting files
file_combobox = ttk.Combobox(root)
canvas.create_window(50, 350, anchor=tk.NW, window=file_combobox)

reboot_button = tk.Button(root, text="Restart ESP32", command=send_reboot_command)
canvas.create_window(50, 400, anchor=tk.NW, window=reboot_button)

# Initial update of the file list
update_file_list()

# Run the application
root.mainloop()