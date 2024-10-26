import socket

def receive_message_from_server():
    HOST = '192.168.178.237'  # Replace with the ESP32's IP address
    PORT = 8080  # The port the server is listening on

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            print(f"Connecting to {HOST}:{PORT}")
            s.connect((HOST, PORT))
            print("Connected to the server")

            # Receive message from the server
            data = s.recv(1024)
            print(f"Received message from server: {data.decode()}")

    except socket.error as e:
        print(f"Socket error: {e}")

receive_message_from_server()