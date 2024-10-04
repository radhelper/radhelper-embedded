import serial
import socket

# Configuration parameters
# url = "socket://130.246.241.133:20108"  # Replace with the correct URL
url = "socket://130.246.241.134:20108"  # Replace with the correct URL
baudrate = 115200  # Set the correct baudrate for your device
ser = None
# url = "130.246.241.134"  # IP address
# port = 20108  # Port number

# try:
#     # Create a socket object
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#         s.settimeout(1)  # Set a timeout for the connection
#         s.connect((url, port))  # Connect to the device

#         # Send some data if needed
#         s.sendall(b"Your command here\n")

#         # Receive data from the device
#         response = s.recv(1024)  # Buffer size
#         print(f"Received: {response.decode()}")
# except socket.timeout:
#     print("Socket connection timed out.")
# except Exception as e:
#     print(f"An error occurred: {e}")


try:
    # Open the serial connection
    ser = serial.serial_for_url(url, baudrate=baudrate, timeout=1)

    print(f"Connected to {url} at baudrate {baudrate}")

    # Read data from the serial port
    while True:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)  # Read available data
            print(
                f"Received: {data.decode('utf-8', errors='ignore')}"
            )  # Print received data

except serial.SerialException as e:
    print(f"Error: {e}")
except KeyboardInterrupt:
    print("Stopping script...")
finally:
    if ser.is_open:
        ser.close()
    print("Serial connection closed.")
