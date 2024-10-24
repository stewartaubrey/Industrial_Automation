import network
import time

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # Check if already connected
    if wlan.isconnected():
        print(f"Already connected to {ssid} with IP address: {wlan.ifconfig()[0]}")
        return

    # Attempt to connect to the Wi-Fi network
    print(f"Connecting to {ssid}...")
    try:
        wlan.connect(ssid, password)
    except Exception as e:
        print(f"Error connecting to {ssid}: {e}")
        return

    # Wait for connection with a timeout
    start_time = time.time()
    while not wlan.isconnected():
        if time.time() - start_time > 10:
            print(f"Failed to connect to {ssid} within timeout")
            return
        print("Connecting...")
        time.sleep(1)

    # Check if connected and print the IP address
    if wlan.isconnected():
        print(f"Successfully connected to {ssid} with IP address: {wlan.ifconfig()[0]}")
    else:
        print(f"Failed to connect to {ssid}")

# Example usage
SSID = 'BorgoPio138'
PASSWORD = 'buongornio'
connect_wifi(SSID, PASSWORD)