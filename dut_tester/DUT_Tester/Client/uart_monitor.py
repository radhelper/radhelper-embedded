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

SERIAL_TIMEOUT = 20
MIN_FRAME_INTERVAL = 2


class UARTMonitor(Thread):
    def __init__(
        self,
        logger: Logger,
        event_heartbeat: Event,
        event_stop: Event,
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

        self.max_buffer_size = 524  ## Equals to 2 maxed frames
        self.frame_package_size = 6

        self.freq = freq
        self.logger = logger

        self.last_serial = time.time()

        self.serial = None

        self.serial_timeout = False

        self.PI = pigpio.pi()

    def run(self):
        self.event_heartbeat.set()

        self.logger.consoleLogger.info(f"Started UART Monitor Thread. [{os.getpid()}]")

        self.serial = self.PI.serial_open(self.tty, self.baudrate)

        self.last_serial = time.time()

        while not self.event_stop.is_set():
            # Set heartbeat signal
            self.event_heartbeat.set()

            frame_buffer = self.read_frame_from_serial()  # This function is blocking
            if frame_buffer is not None:
                try:
                    frame_buffer_hex = frame_buffer.decode("utf-8")
                except:
                    frame_buffer_hex = str(binascii.hexlify(d), "ascii")

                # don't log unless is a complete frame or abandoned frame
                # self.logger.dataLogger.info(
                #     {
                #         "type": "Serial",
                #         "id": CLIENT_SERIAL_FRAME_RX,
                #         "timestamp": time.time(),
                #         "data": frame_buffer_hex,
                #     }
                # )
                self.logger.consoleLogger.info(
                    "[Serial] " + frame_buffer_hex.rstrip("\n")
                )

                #### process the received loop and check for frames
                # would be good to at least check for double frames...

                self.check_for_frame(frame_buffer)

            else:
                # log error or something else.
                continue

            time.sleep(1 / self.freq)  # do I need this???

        self.PI.serial_close(self.serial)
        self.logger.consoleLogger.info(f"Stopped Data Monitor Thread. [{os.getpid()}]")

    ##### loop to listen to port
    # does not quit until the serial port goes quiet for a while
    # timeout if nothing gets sent for a while
    # max buffer size to prevent infinite read
    # log every received buffer
    def read_frame_from_serial(self):
        partial_frame_buffer = bytearray()
        frame_received = False

        while True:
            data_avaiable = self.PI.serial_data_available(self.serial)

            if data_avaiable:
                self.serial_timeout = False
                self.last_serial = time.time()
                _, d = self.PI.serial_read(self.serial)
                partial_frame_buffer += d

                # Check for buffer overflow
                if len(partial_frame_buffer) > self.max_buffer_size:
                    # Handle buffer overflow (e.g., clear buffer, log error)
                    break

            # Check for dead transmitter
            if (
                time.time() - self.last_serial > SERIAL_TIMEOUT
                and not self.serial_timeout
            ):
                self.serial_timeout = True
                self.logger.consoleLogger.warn("Serial Communication Timeout!")
                self.logger.dataLogger.info(
                    {
                        "type": "Serial",
                        "id": CLIENT_SERIAL_TIMEOUT,
                        "timestamp": time.time(),
                        "event": "Serial Timeout",
                    }
                )

                ## If dead: power cycle the DUT
                # ps.power_cycle("192.168.0.1", 1)
                frame_received = False

                break
            # if not dead transmiter, means the frame transmission just ended
            elif time.time() - self.last_serial > MIN_FRAME_INTERVAL:
                frame_received = True
                break

            time.sleep(1 / self.freq)

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
                    "type": "Serial",
                    "id": CLIENT_SERIAL_FRAME_RX,
                    "timestamp": time.time(),
                    "data": buffer,
                }
            )
        else:
            self.logger.dataLogger.info(
                {
                    "type": "Serial",
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

        if crc_check is False:
            self.logger.consoleLogger.info(f"CRC Check failed!")

        self.logger.dataLogger.info(
            {
                "type": "Serial",
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
