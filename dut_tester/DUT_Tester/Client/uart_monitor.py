import binascii
import os
import time
from threading import Event, Thread

import serial

from DUT_Tester.log_id import (
    CLIENT_SERIAL_TIMEOUT,
    CLIENT_SERIAL_FRAME_RX,
    CLIENT_SERIAL_FRAME_ERROR,
)
from DUT_Tester.util import Logger

from DUT_Tester.crc_table import crcTable

from DUT_Tester.power_switch.error_codes import ErrorCodes
import DUT_Tester.power_switch.powerswitch as ps
from DUT_Tester.Client.payload_decoding import parse_payload

SERIAL_TIMEOUT = 10
MIN_FRAME_INTERVAL = 2
SLEEP_AFTER_REBOOT = 20


class UARTMonitor(Thread):
    def __init__(
        self,
        logger: Logger,
        event_heartbeat: Event,
        event_stop: Event,
        name="",
        freq=100,
        tty="/dev/ttyUSB0",
        baudrate=115200,
        lindy_switch="192.168.1.240",
        lindy_port=1,
    ):
        Thread.__init__(self)
        self.deamon = True
        self.event_heartbeat = event_heartbeat
        self.event_stop = event_stop
        self.baudrate = baudrate
        self.tty = tty
        self.name = name
        self.lindy_switch = lindy_switch
        self.lindy_port = lindy_port

        self.max_buffer_size = 524  ## Equals to 2 maxed frames
        self.frame_package_size = 6

        self.freq = freq
        self.logger = logger

        self.last_serial = time.time()

        self.reboot_start_time = time.time() - 10

        # self.DUT_rebooting = False

        self.serial = None

        self.serial_timeout = False
        self.device_is_off = True

        # self.PI = pigpio.pi()

    def run(self):
        self.event_heartbeat.set()

        self.logger.consoleLogger.info(
            f'Started UART "{self.name}" Monitor Thread. [{os.getpid()}]'
        )

        self.serial = serial.Serial(port=self.tty, baudrate=self.baudrate)

        self.serial.flushInput()
        self.serial.flushOutput()

        self.last_serial = time.time()

        self.power_up_DUT(self.lindy_port, self.lindy_switch)

        while not self.event_stop.is_set():
            # Set heartbeat signal
            self.event_heartbeat.set()

            frame_buffer = (
                self.read_frame_from_serial()
            )  # This function is blocking for at least SERIAL_TIMEOUT and at max SERIAL_TIMEOUT

            if frame_buffer is not None:
                try:
                    frame_buffer_hex = frame_buffer.decode("utf-8")
                except:
                    frame_buffer_hex = str(binascii.hexlify(frame_buffer), "ascii")

                # don't log unless is a complete frame or abandoned frame
                self.logger.dataLogger.info(
                    {
                        "type": "Serial " + self.name,
                        "id": CLIENT_SERIAL_FRAME_RX,
                        "timestamp": time.time(),
                        "data": frame_buffer_hex,
                    }
                )
                self.logger.consoleLogger.info(
                    "[Serial] " + self.name + " " + frame_buffer_hex.rstrip("\n")
                )
                #### process the received loop and check for frames
                # would be good to at least check for double frames...
                # self.check_for_frame(frame_buffer)

            else:  ## If its not getting anything, try powering up
                self.power_up_DUT(self.lindy_port, self.lindy_switch)

        # self.PI.serial_close(self.serial)
        self.serial.close()
        self.logger.consoleLogger.info(f"Stopped Data Monitor Thread. [{os.getpid()}]")

    ##### loop to listen to port
    # does not quit until the serial port goes quiet for a while
    # timeout if nothing gets sent for a while
    # max buffer size to prevent infinite read
    # log every received buffer

    def read_frame_from_serial(self):
        frame_buffer = bytearray()
        last_read_time = None

        while not self.event_stop.is_set():
            self.event_heartbeat.set()

            # Check for data availability
            if self.serial.in_waiting > 0:
                self.serial_timeout = False
                data = self.serial.read(self.serial.in_waiting)
                frame_buffer += data

                # Update the last read time
                last_read_time = time.time()

            # Check if the frame interval has elapsed
            if last_read_time and time.time() - last_read_time > 3:
                if len(frame_buffer) > 0:
                    return frame_buffer
                else:
                    # Reset for the next frame
                    frame_buffer = bytearray()

            # Handle potential buffer overflow
            if len(frame_buffer) > self.max_buffer_size:
                self.logger.consoleLogger.warn("Receiver buffer overflow!")
                return frame_buffer

            # Check for serial timeout
            if (
                last_read_time
                and time.time() - last_read_time > SERIAL_TIMEOUT
                and not self.serial_timeout
            ):
                self.handle_serial_timeout()
                return None

            # time.sleep(0.001)  # Sleep for 100 ms to reduce CPU usage

        return None

    def handle_serial_timeout(self):
        self.serial_timeout = True
        self.logger.consoleLogger.warn("Serial Communication Timeout!")
        self.logger.dataLogger.info(
            {
                "type": "Serial " + self.name,
                "id": CLIENT_SERIAL_TIMEOUT,
                "timestamp": time.time(),
                "event": "Serial Timeout",
            }
        )
        self.power_down_DUT(self.lindy_port, self.lindy_switch)

    def check_for_frame(self, buffer):
        # Read byte by byte

        frame_buffer = bytearray()
        in_frame = False
        frame_processed_successfully = False
        payload_length = 0
        bytes_read = 0
        buffer_size = len(buffer)

        for byte in buffer:
            if byte == 0xAA:  # Start of frame
                in_frame = True
                frame_buffer.append(byte)
                bytes_read = 1
            elif in_frame:
                frame_buffer.append(byte)
                bytes_read += 1
                if bytes_read == 3:  # Assuming the second byte is payload_length
                    payload_length = byte
                    if buffer_size == (payload_length + self.frame_package_size):
                        frame_fully_received = True
                        # this might be useless now... or use it to check for double payload
                        # TODO: check for double frames based on size.

                if (
                    bytes_read > 3
                    and bytes_read == payload_length + self.frame_package_size
                ):  # +5 for start_of_frame, frame_id, payload_length, and crc16
                    if byte == 0x55:  # End of frame
                        self.decode_frame(frame_buffer)
                        frame_processed_successfully = True
                        in_frame = False
                    else:  # Incorrect end of frame byte
                        self.logger.consoleLogger.warn(
                            "Frame error: Incorrect end of frame byte"
                        )
                        in_frame = False
                        frame_processed_successfully = False

                # Check if this is the last byte but still in a frame
                if bytes_read == buffer_size and in_frame:
                    self.logger.consoleLogger.warn(
                        "Frame error: Incomplete frame at end of buffer"
                    )
                    frame_processed_successfully = False

        if frame_processed_successfully:
            self.logger.dataLogger.info(
                {
                    "type": "Serial " + self.name,
                    "id": CLIENT_SERIAL_FRAME_RX,
                    "timestamp": time.time(),
                    "data": buffer,
                }
            )
        else:
            self.logger.dataLogger.info(
                {
                    "type": "Serial " + self.name,
                    "id": CLIENT_SERIAL_FRAME_ERROR,
                    "timestamp": time.time(),
                    "event": "Frame incomplete",
                }
            )

    def decode_frame(self, frame_bytes):
        # Desconstructing the frame
        header = frame_bytes[0]
        frame_id = frame_bytes[1]
        payload_length = frame_bytes[2]
        payload = frame_bytes[3 : 3 + payload_length]
        crc_bytes = frame_bytes[3 + payload_length : 5 + payload_length]
        tail = frame_bytes[-1]

        # Concatenating the CRC bytes into a single number
        # Assuming CRC is in big-endian format
        crc = (crc_bytes[0] << 8) | crc_bytes[1]

        # Converting payload to hex representation
        payload_hex = [hex(byte) for byte in payload]

        crc_check = self.check_crc(payload, payload_length, crc)

        data = None

        if crc_check is False:
            self.logger.consoleLogger.info(f"CRC Check failed!")
        else:
            data = parse_payload(payload, frame_id)

        self.logger.dataLogger.info(
            {
                "type": "Serial " + self.name,
                "frame type": frame_id,
                "CRC check": crc_check,
                "Payload": payload_hex,
            }
        )

    def check_crc(self, payload, payload_length, crc_value):
        INITIAL_REMAINDER = 0xFFFF
        FINAL_XOR_VALUE = 0x0000
        remainder = INITIAL_REMAINDER

        for byte in range(payload_length):
            data = payload[byte] ^ (remainder >> (16 - 8))
            remainder = crcTable[data] ^ (remainder << 8) & 0xFFFF

        return crc_value == (remainder ^ FINAL_XOR_VALUE)

    def power_down_DUT(self, select_power_switch, power_IP):
        return_code = 0
        return_code = ps._lindy_switch("OFF", select_power_switch, power_IP)

        self.device_is_off = True

        self.reboot_start_time = time.time()

        self.logger.consoleLogger.warn(
            f"Powering down {select_power_switch} at {power_IP}:: {return_code}"
        )

    def power_up_DUT(self, select_power_switch, power_IP):
        return_code = 0

        if (time.time() > self.reboot_start_time + 10) and self.device_is_off == True:
            # print(self.reboot_start_time, time.time())
            return_code = ps._lindy_switch("ON", select_power_switch, power_IP)

            self.logger.consoleLogger.warn(
                f"Powering up {select_power_switch} at {power_IP}:: {return_code}"
            )
            self.device_is_off = False

        if time.time() > self.reboot_start_time + 20:
            self.serial_timeout = False
