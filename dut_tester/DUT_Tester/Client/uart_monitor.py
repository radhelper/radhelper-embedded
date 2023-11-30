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

        self.crcTable = [
            0x0000,
            0x1021,
            0x2042,
            0x3063,
            0x4084,
            0x50A5,
            0x60C6,
            0x70E7,
            0x8108,
            0x9129,
            0xA14A,
            0xB16B,
            0xC18C,
            0xD1AD,
            0xE1CE,
            0xF1EF,
            0x1231,
            0x0210,
            0x3273,
            0x2252,
            0x52B5,
            0x4294,
            0x72F7,
            0x62D6,
            0x9339,
            0x8318,
            0xB37B,
            0xA35A,
            0xD3BD,
            0xC39C,
            0xF3FF,
            0xE3DE,
            0x2462,
            0x3443,
            0x0420,
            0x1401,
            0x64E6,
            0x74C7,
            0x44A4,
            0x5485,
            0xA56A,
            0xB54B,
            0x8528,
            0x9509,
            0xE5EE,
            0xF5CF,
            0xC5AC,
            0xD58D,
            0x3653,
            0x2672,
            0x1611,
            0x0630,
            0x76D7,
            0x66F6,
            0x5695,
            0x46B4,
            0xB75B,
            0xA77A,
            0x9719,
            0x8738,
            0xF7DF,
            0xE7FE,
            0xD79D,
            0xC7BC,
            0x48C4,
            0x58E5,
            0x6886,
            0x78A7,
            0x0840,
            0x1861,
            0x2802,
            0x3823,
            0xC9CC,
            0xD9ED,
            0xE98E,
            0xF9AF,
            0x8948,
            0x9969,
            0xA90A,
            0xB92B,
            0x5AF5,
            0x4AD4,
            0x7AB7,
            0x6A96,
            0x1A71,
            0x0A50,
            0x3A33,
            0x2A12,
            0xDBFD,
            0xCBDC,
            0xFBBF,
            0xEB9E,
            0x9B79,
            0x8B58,
            0xBB3B,
            0xAB1A,
            0x6CA6,
            0x7C87,
            0x4CE4,
            0x5CC5,
            0x2C22,
            0x3C03,
            0x0C60,
            0x1C41,
            0xEDAE,
            0xFD8F,
            0xCDEC,
            0xDDCD,
            0xAD2A,
            0xBD0B,
            0x8D68,
            0x9D49,
            0x7E97,
            0x6EB6,
            0x5ED5,
            0x4EF4,
            0x3E13,
            0x2E32,
            0x1E51,
            0x0E70,
            0xFF9F,
            0xEFBE,
            0xDFDD,
            0xCFFC,
            0xBF1B,
            0xAF3A,
            0x9F59,
            0x8F78,
            0x9188,
            0x81A9,
            0xB1CA,
            0xA1EB,
            0xD10C,
            0xC12D,
            0xF14E,
            0xE16F,
            0x1080,
            0x00A1,
            0x30C2,
            0x20E3,
            0x5004,
            0x4025,
            0x7046,
            0x6067,
            0x83B9,
            0x9398,
            0xA3FB,
            0xB3DA,
            0xC33D,
            0xD31C,
            0xE37F,
            0xF35E,
            0x02B1,
            0x1290,
            0x22F3,
            0x32D2,
            0x4235,
            0x5214,
            0x6277,
            0x7256,
            0xB5EA,
            0xA5CB,
            0x95A8,
            0x8589,
            0xF56E,
            0xE54F,
            0xD52C,
            0xC50D,
            0x34E2,
            0x24C3,
            0x14A0,
            0x0481,
            0x7466,
            0x6447,
            0x5424,
            0x4405,
            0xA7DB,
            0xB7FA,
            0x8799,
            0x97B8,
            0xE75F,
            0xF77E,
            0xC71D,
            0xD73C,
            0x26D3,
            0x36F2,
            0x0691,
            0x16B0,
            0x6657,
            0x7676,
            0x4615,
            0x5634,
            0xD94C,
            0xC96D,
            0xF90E,
            0xE92F,
            0x99C8,
            0x89E9,
            0xB98A,
            0xA9AB,
            0x5844,
            0x4865,
            0x7806,
            0x6827,
            0x18C0,
            0x08E1,
            0x3882,
            0x28A3,
            0xCB7D,
            0xDB5C,
            0xEB3F,
            0xFB1E,
            0x8BF9,
            0x9BD8,
            0xABBB,
            0xBB9A,
            0x4A75,
            0x5A54,
            0x6A37,
            0x7A16,
            0x0AF1,
            0x1AD0,
            0x2AB3,
            0x3A92,
            0xFD2E,
            0xED0F,
            0xDD6C,
            0xCD4D,
            0xBDAA,
            0xAD8B,
            0x9DE8,
            0x8DC9,
            0x7C26,
            0x6C07,
            0x5C64,
            0x4C45,
            0x3CA2,
            0x2C83,
            0x1CE0,
            0x0CC1,
            0xEF1F,
            0xFF3E,
            0xCF5D,
            0xDF7C,
            0xAF9B,
            0xBFBA,
            0x8FD9,
            0x9FF8,
            0x6E17,
            0x7E36,
            0x4E55,
            0x5E74,
            0x2E93,
            0x3EB2,
            0x0ED1,
            0x1EF0,
        ]

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

        print(self.check_crc(payload, payload_length, crc))

        print(f"Header: {hex(header)}")
        print(f"Payload Length: {hex(payload_length)}")
        print(f"Frame ID: {hex(frame_id)}")
        print(f"Payload: {payload_hex}")
        print(f"CRC: {hex(crc)}")
        print(f"Tail: {hex(tail)}")

        self.logger.consoleLogger.info(
            {
                "type": "Serial",
                "event": frame_id,
            }
        )

    def check_crc(self, payload, payload_length, crc_value):
        INITIAL_REMAINDER = 0xFFFFFFFF
        FINAL_XOR_VALUE = 0xFFFFFFFF
        remainder = INITIAL_REMAINDER

        for byte in range(payload_length):
            data = payload[byte] ^ (remainder >> (16 - 8))
            remainder = self.crcTable[data] ^ (remainder << 8) & 0xFFFF

        print(remainder ^ FINAL_XOR_VALUE)

        return crc_value == (remainder ^ FINAL_XOR_VALUE)
