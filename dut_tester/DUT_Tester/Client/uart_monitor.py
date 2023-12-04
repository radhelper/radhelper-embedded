import binascii
import os
import time
from threading import Event, Thread

import pigpio

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

SERIAL_TIMEOUT = 15
MIN_FRAME_INTERVAL = 0.5
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
    ):
        Thread.__init__(self)
        self.deamon = True
        self.event_heartbeat = event_heartbeat
        self.event_stop = event_stop
        self.baudrate = baudrate
        self.tty = tty
        self.name = name

        self.max_buffer_size = 524  ## Equals to 2 maxed frames
        self.frame_package_size = 6

        self.freq = freq
        self.logger = logger

        self.last_serial = time.time()

        # self.DUT_rebooting = False

        self.serial = None

        self.serial_timeout = False

        self.PI = pigpio.pi()

    def run(self):
        self.event_heartbeat.set()

        self.logger.consoleLogger.info(
            f'Started UART "{self.name}" Monitor Thread. [{os.getpid()}]'
        )

        self.serial = self.PI.serial_open(self.tty, self.baudrate)

        self.last_serial = time.time()

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
                self.check_for_frame(frame_buffer)

            # if self.DUT_rebooting == True:
            #     break  # quit thread

            time.sleep(1 / self.freq)  # do I need this???

        self.PI.serial_close(self.serial)
        self.logger.consoleLogger.info(f"Stopped Data Monitor Thread. [{os.getpid()}]")

    ##### loop to listen to port
    # does not quit until the serial port goes quiet for a while
    # timeout if nothing gets sent for a while
    # max buffer size to prevent infinite read
    # log every received buffer
    def read_frame_from_serial(self):
        frame_received = False
        # partial_frame_buffer = None
        partial_frame_buffer = bytearray()
        serial_port_busy = True

        while not self.event_stop.is_set() and serial_port_busy == True:
            self.event_heartbeat.set()
            data_avaiable = self.PI.serial_data_available(self.serial)
            if data_avaiable:
                self.serial_timeout = False
                self.last_serial = time.time()
                len_d, d = self.PI.serial_read(self.serial)
                if len_d > 0:
                    partial_frame_buffer += d
                else:
                    print(partial_frame_buffer)

                # Check for buffer overflow
                if len(partial_frame_buffer) > self.max_buffer_size:
                    self.logger.consoleLogger.warn("Receiver buffer overflow!")
                    ## TODO: SHOULD WE ADD A DATA LOG FOR THE OVERFLOW BUFF?
                    return partial_frame_buffer

            # Check for dead transmitter
            if (
                time.time() - self.last_serial > SERIAL_TIMEOUT
                and not self.serial_timeout
            ):
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

                self.reboot_DUT()

                frame_received = False
                serial_port_busy = False
            # if not dead transmiter, means the frame transmission just ended
            elif (
                time.time() - self.last_serial > MIN_FRAME_INTERVAL
                and len(partial_frame_buffer) > self.frame_package_size
            ):
                frame_received = True
                serial_port_busy = False
            else:
                serial_port_busy = True

            # time.sleep(1 / self.freq)

        # return partial_frame_buffer

        if frame_received == True:
            return partial_frame_buffer
        else:
            return None

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

    def reboot_DUT(self):
        # Close serial port
        # self.logger.consoleLogger.info(f"Killing uart connection.")
        # self.PI.serial_close(self.serial)

        # self.DUT_rebooting = True
        self.logger.consoleLogger.info(f"Power Cycling DUT.")
        # Power cycle DUT
        # ps.power_cycle("192.168.0.1", 1)

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
            print(type(payload))
            data = parse_payload(payload, frame_id)
            print(data)

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
