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
TIMEOUT = 150

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


# Register an handler for the timeout
def handler(signum, frame):
    raise Exception("Timout on the receiver!")


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
