from serial import Serial
import struct
import requests
import time
import datetime
import os
import signal
import json
import sys

serial_port_num = 0
serial_port = "/dev/ttyUSB"
serial_baud = 19200
file_log = "./log/SEM_NEO_SCRUB_"
# file_log = "./SEM_NEO_NOSCRUB_"
runs_per_file = 2
num_runs = 0
reboot = False
start_flag = False
log = 0
is_kria = False
TIMEOUT = 300

align_start = 0xF0
align_end = 0xAB
power_switch = 0
align_start_count = 0
align_end_count = 0

__ON = "ON"
__OFF = "OFF"
_H = 8
_G = 7


# Check if an argument is provided
if len(sys.argv) != 2:
    print("Provide a TTY port number")
    sys.exit(1)

# Get the argument as a string
serial_port_num = sys.argv[1]

power_IP = "192.168.1.120"

if serial_port_num == str(1):
    power_switch = _G
    power_IP = "192.168.1.120"
elif serial_port_num == str(0):
    power_switch = _H
    power_IP = "192.168.1.120"
elif serial_port_num == str(2):
    is_kria = True

serial_port = serial_port + str(serial_port_num)

# Use the argument in your code
print("Selected TTY:", serial_port)
# ... rest of your code using the argument ...


def _lindy_switch(status: str, switch_port: int, switch_ip: str):
    """Lindy switch reboot rules
    :param status: ON or OFF
    :param switch_port: port to reboot
    :param switch_ip: ip address for the switch
    :param logger: logging.Logger obj
    :return: ErrorCodes enum
    """
    # before: led = f"{to_change[:(switch_port - 1)]}1{to_change[switch_port:]}"
    to_change = list("000000000000000000000000")
    to_change[switch_port - 1] = "1"
    led = "".join(to_change)
    if status == __ON:
        # TODO: Check if lindy switch accepts https protocol
        url = f"http://{switch_ip}/ons.cgi?led={led}"
    else:
        url = f"http://{switch_ip}/offs.cgi?led={led}"
    payload = {
        "led": led,
    }
    headers = {
        "Host": switch_ip,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:56.0) Gecko/20100101 Firefox/56.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Referer": f"http://{switch_ip}/outlet.htm",
        "Authorization": "Basic c25tcDoxMjM0",
        "Connection": "keep-alive",
        "Content-Length": "0",
    }

    # print(url)
    # print(headers)
    default_string = "Could not change Lindy IP switch status, portNumber:"
    try:
        requests_status = requests.post(url, data=json.dumps(payload), headers=headers)
        requests_status.raise_for_status()
        # reboot_status = ErrorCodes.SUCCESS
    except requests.exceptions.HTTPError as http_error:
        print("Error on Lindy")
        # reboot_status = ErrorCodes.HTTP_ERROR
        # logger.error(
        #     f"{default_string} {switch_port} status:{reboot_status} switchIP:{switch_ip} error:{http_error}"
        # )
    except requests.exceptions.ConnectionError as connection_error:
        print("Error on Lindy")
        # reboot_status = ErrorCodes.CONNECTION_ERROR
        # logger.error(
        #     f"{default_string} {switch_port} status:{reboot_status} switchIP:{switch_ip} error:{connection_error}"
        # )
    except requests.exceptions.Timeout as timeout_error:
        print("Error on Lindy")
        # reboot_status = ErrorCodes.TIMEOUT_ERROR
        # logger.error(
        #     f"{default_string} {switch_port} status:{reboot_status} switchIP:{switch_ip} error:{timeout_error}"
        # )
    except requests.exceptions.RequestException as general_error:
        print("Error on Lindy")
        # reboot_status = ErrorCodes.GENERAL_ERROR
        # logger.error(
        #     f"{default_string} {switch_port} status:{reboot_status} switchIP:{switch_ip} error:{general_error}"
        # )
    return 0


# Register an handler for the timeout
def handler(signum, frame):
    raise Exception("Timout on the receiver!")


def power_cycle(select_power_switch, power_IP):
    return_code = 0
    return_code = _lindy_switch("OFF", select_power_switch, power_IP)
    print("Powering down..", select_power_switch)
    time.sleep(10)
    return_code = _lindy_switch("ON", select_power_switch, power_IP)
    print("Powering up..", select_power_switch)
    time.sleep(10)
    return return_code


def check_bytes(hex_number):
    # if len(hex_number) != 8:
    #     raise ValueError("Hexadecimal number must have a length of 8 characters.")

    pattern = 0xF0F0

    pattern = hex_number[:4]
    pattern = hex_number[4:]
    if pattern == hex_number:
        return 0
    elif pattern == hex_number[4:]:
        return 2
    elif pattern == hex_number[:4]:
        return 4
    else:
        return 14


def count_alignment(number):
    byte1 = (number >> 24) & 0xFF
    byte2 = (number >> 16) & 0xFF
    byte3 = (number >> 8) & 0xFF
    byte4 = number & 0xFF

    global align_start_count
    global align_end_count

    if byte1 == 0xF0:
        align_start_count += 1
    if byte2 == 0xF0:
        align_start_count += 1
    if byte3 == 0xF0:
        align_start_count += 1
    if byte4 == 0xF0:
        align_start_count += 1
    # print(align_start_count)

    if byte1 == 0xAB:
        align_end_count += 1
    if byte2 == 0xAB:
        align_end_count += 1
    if byte3 == 0xAB:
        align_end_count += 1
    if byte4 == 0xAB:
        align_end_count += 1

    if align_start_count > 5:
        align_start_count = 0
        return 1
    elif align_end_count > 5:
        align_end_count = 0
        return 0
    else:
        return -1

    # return byte1, byte2, byte3, byte4


def ignore_bootloader_2(serial):
    byte2 = struct.unpack("B", serial.read(1))[0]
    byte1 = struct.unpack("B", serial.read(1))[0]


def burst_4(serial):
    byte4 = struct.unpack("B", serial.read(1))[0]
    byte3 = struct.unpack("B", serial.read(1))[0]
    byte2 = struct.unpack("B", serial.read(1))[0]
    byte1 = struct.unpack("B", serial.read(1))[0]

    # print(hex(byte4), hex(byte3), hex(byte2), hex(byte1))
    number = (byte4 << 24) + (byte3 << 16) + (byte2 << 8) + (byte1)

    return number


def read_to_align(serial, number_of_reads):
    for i in range(number_of_reads):
        struct.unpack("B", serial.read(1))[0]


def open_serial():
    serial = Serial(
        serial_port, serial_baud, 8, "N", 1
    )  ### This serial port name may be various on OS or machine

    if serial.is_open:
        print(serial_port, serial_baud)

    serial.flushInput()
    serial.flushOutput()

    return serial


def character(serial):
    character = struct.unpack("B", serial.read(1))[0]

    print(chr(character))


serial = open_serial()


power_cycle(power_switch, power_IP)


while True:
    file_iteration = file_log + "{:03}".format(log) + ".txt"

    # Register the signal function handler
    signal.signal(signal.SIGALRM, handler)

    while os.path.isfile(file_iteration):
        log += 1
        file_iteration = file_log + "{:03}".format(log) + ".txt"
    f = open(file_iteration, "a+")

    print(datetime.datetime.now())
    print(datetime.datetime.now(), file=f)

    number_of_reads = 0

    while True:
        # Define a timeout for your function
        signal.alarm(TIMEOUT)

        valid_input = False

        try:
            number = burst_4(serial)
            valid_input = True
            # dosomething
        except Exception as exc:
            print(exc)
            print(exc, file=f)
            print(datetime.datetime.now(), file=f)

        # Cancel the timer if the function returned before timeout
        signal.alarm(0)

        if valid_input:
            aligned = count_alignment(number)
            if aligned == 1:
                print("Start of iteration")
                num_runs += 1
                print(datetime.datetime.now())
                print(datetime.datetime.now(), file=f)
            elif aligned == 0:
                print("Ending iteration")
            # if number == 0xF0F0F0F0:
            #     if start_flag == False:
            #         start_flag = True
            #     elif start_flag == True:
            #         print(datetime.datetime.now())
            #         # f.write(str(datetime.datetime.now()))
            #         print(datetime.datetime.now(), file=f)
            #         start_flag = False

            print(hex(number), file=f)
            print(hex(number))

            if num_runs > runs_per_file:
                f.close()
                num_runs = 0
                print("//////// FINISHED RUN ////////////")
                break
        else:
            f.close()
            if is_kria == False:
                print("To be sure")
                power_cycle(power_switch, power_IP)
            reboot = True
            num_runs = 0

            break

    log += 1

f.close()

# serial.flushInput()
# serial.flushOutput()

# serial.close()
# now = datetime.datetime.now()

# print(now)


# import serial
# import io

# # import multiprocessing
# import threading
# import time


# # reads lines in a separate thread to avoid locking
# # kill it with a timeout to insure everything gets printed
# def thread_read_lines(ser):
#     sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

#     while True:
#         # read raw data
#         # 		data = ser.read(1000)
#         # 		if (data):
#         # 			print(data)

#         # read formated data
#         data = None
#         try:
#             data = sio.readline(1000)
#         except:
#             print("Data could not be read")
#             time.sleep(1)

#         if data:
#             print(data, end="")


# if __name__ == "__main__":
#     with serial.Serial("/dev/ttyACM0", 9600, timeout=1) as ser:
#         print(ser.name)
#         print(ser.is_open)

#         # p = multiprocessing.Process(target=read_lines, name="read_lines", args=(ser,))
#         p = threading.Thread(target=thread_read_lines, args=(ser,))
#         p.daemon = True

#         p.start()

#         p.join()  # timeout to kill the function

#         # If thread is active
#         if p.is_alive():
#             print("Print is running for more than 10 sec. Killing it")

#             # Terminate foo
#             p.terminate()
#             p.join()
