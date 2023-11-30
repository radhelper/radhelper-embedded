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

        self.freq = freq
        self.logger = logger

        self.last_serial = time.time()

        self.serial_timeout = False

        self.PI = pigpio.pi()

    def run(self):
        self.event_heartbeat.set()

        self.logger.consoleLogger.info(f"Started UART Monitor Thread. [{os.getpid()}]")

        self.last_serial = time.time()

        serial = self.PI.serial_open(self.tty, self.baudrate)

        while not self.event_stop.is_set():
            # Set heartbeat signal
            self.event_heartbeat.set()

            data_avaiable = self.PI.serial_data_available(serial)
            if data_avaiable:
                _, d = self.PI.serial_read(serial)
                # d = d.rstrip(b"\x00")
                if len(d) > 0:
                    self.serial_timeout = False
                    self.last_serial = time.time()

                    try:
                        string = d.decode("utf-8")
                    except:
                        string = str(binascii.hexlify(d), "ascii")
                    self.logger.dataLogger.info(
                        {
                            "type": "Serial",
                            "id": CLIENT_SERIAL_FRAME_RX,
                            "timestamp": time.time(),
                            "data": string,
                        }
                    )
                    self.logger.consoleLogger.info("[Serial] " + string.rstrip("\n"))

                    self.check_for_frame(d)

                    # self.logger.dataLogger.info(
                    #     {
                    #         "type": "Serial",
                    #         "id": CLIENT_SERIAL_FRAME_RX,
                    #         "timestamp": time.time(),
                    #         "data": d,
                    #     }
                    # )
                    # self.logger.consoleLogger.info("[Serial] " + d.rstrip("\n"))

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

                ## ADD POWER CYCLE
                # ps.power_cycle("192.168.0.1", 1)

            time.sleep(1 / self.freq)

        self.PI.serial_close(serial)
        self.logger.consoleLogger.info(f"Stopped Data Monitor Thread. [{os.getpid()}]")

    def check_for_frame(self, buffer):
        # Read byte by byte

        frame_buffer = bytearray()
        in_frame = False
        payload_length = 0
        bytes_read = 0

        for byte in buffer:
            if byte == 0xAA:  # Start of frame
                in_frame = True
                frame_buffer.append(byte)
                bytes_read = 0
            elif in_frame:
                frame_buffer.append(byte)
                bytes_read += 1
                if bytes_read == 2:  # Assuming the second byte is payload_length
                    payload_length = byte

                if (
                    bytes_read > 2 and bytes_read == payload_length + 5
                ):  # +3 for start_of_frame, frame_id, and payload_length itself
                    if byte == 0x55:  # End of frame
                        self.decode_frame(frame_buffer)
                        in_frame = False
                    else:
                        self.logger.consoleLogger.warn(
                            "Frame error: Incorrect end of frame byte"
                        )
                        in_frame = False

    def decode_frame(self, frame_bytes):
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

        # print(f"Header: {hex(header)}")
        # print(f"Payload Length: {hex(payload_length)}")
        # print(f"Frame ID: {hex(frame_id)}")
        # print(f"Payload: {payload_hex}")
        # print(f"CRC: {hex(crc)}")
        # print(f"Tail: {hex(tail)}")

        self.logger.consoleLogger.info(
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
