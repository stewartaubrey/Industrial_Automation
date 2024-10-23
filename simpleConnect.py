import network
import time

# Define the SSID and password for the Wi-Fi network
SSID = 'BorgoPio138'
PASSWORD = 'buongornio'
#ssid1 = 'BorgoPio138'
#password1 = 'buongornio

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # Check if already connected
    if wlan.isconnected():
        print(f"Already connected to {ssid} with IP address: {wlan.ifconfig()[0]}")
        return

    # Attempt to connect to the Wi-Fi network
    print(f"Connecting to {ssid}...")
    wlan.connect(ssid, password)

    # Wait for connection with a timeout
    start_time = time.time()
    while not wlan.isconnected():
        if time.time() - start_time > 10:
            print(f"Failed to connect to {ssid} within timeout")
            return
        print("Connecting...")
        time.sleep(1)

    # Print the IP address once connected
    if wlan.isconnected():
        print(f"Connected to {ssid} with IP address: {wlan.ifconfig()[0]}")
    else:
        print(f"Failed to connect to {ssid}")

# Call the function to connect to Wi-Fi
connect_wifi(SSID, PASSWORD)