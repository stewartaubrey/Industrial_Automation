import tkinter as tk
from tkinter import filedialog, messagebox, ttk
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
    except Exception as e:
        print(f"Error: {e}")

def select_and_send_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        send_file(file_path)

def send_file(file_path):
    file_name = os.path.basename(file_path)
    try:
        s = socket.socket()
        s.connect((HOST, PORT))
        s.sendall(f'SEND_FILE {file_name}'.encode())
        
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                s.sendall(data)
        s.close()
    except Exception as e:
        print(f"Error: {e}")

def update_file_list():
    try:
        s = socket.socket()
        s.connect((HOST, PORT))
        s.sendall(b'LIST_FILES')
        
        file_list = []
        while True:
            data = s.recv(1024).decode()
            if not data:
                break
            file_list.extend(data.split('\n'))
        s.close()
        
        file_combobox['values'] = file_list
    except Exception as e:
        print(f"Error: {e}")

def clear_files_on_esp32():
    try:
        s = socket.socket()
        s.connect((HOST, PORT))
        s.sendall(b'CLEAR_FILES')
        s.close()
    except Exception as e:
        print(f"Error: {e}")

def send_selected_file():
    file_name = file_combobox.get()
    if file_name:
        try:
            s = socket.socket()
            s.connect((HOST, PORT))
            s.sendall(f'SEND_FILE {file_name}'.encode())
            s.close()
            update_file_list()
        except Exception as e:
            print(f"Error: {e}")
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
            update_file_list()
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("No file selected")

def send_reboot_command():
    try:
        s = socket.socket()
        s.connect((HOST, PORT))
        s.sendall(b'REBOOT')
        s.close()
    except Exception as e:
        print(f"Error: {e}")

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

receive_button = tk.Button(root, text="Download from ESP32", command=run_receiver)
receive_button.pack(padx=100, pady=10)

send_button = tk.Button(root, text="Upload New File to ESP32", command=select_and_send_file)
send_button.pack(pady=10)

list_button = tk.Button(root, text="Refresh ESP32 File List", command=update_file_list)
list_button.pack(pady=10)

clear_button = tk.Button(root, text="Delete All Files", command=clear_files_on_esp32)
clear_button.pack(pady=0)

# Add a separator
separator = ttk.Separator(root, orient='horizontal')
separator.pack(fill='x', pady=0)

# Add title for the combobox
combobox_title = tk.Label(root, text="Select File to Send to CNC or Delete from ESP32", font=("Helvetica", 8))
combobox_title.pack(pady=10)

# Create the combobox
file_combobox = ttk.Combobox(root)
file_combobox.pack(pady=0)

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