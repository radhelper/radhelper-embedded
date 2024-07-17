from devices.strategies.device_strategy import DeviceStrategy
from queue import Queue
from time import sleep
import serial
import threading
from frame.frame_decoder import PacketFrame


class TTYStrategy(DeviceStrategy):
    """
    Concrete strategy for TTY device communication.
    """

    def __init__(self, dut_info):
        """
        Initialize TTYStrategy with DUT information.

        Args:
            dut_info (dict): Dictionary containing DUT information.
        """
        self.tty = dut_info["tty"]
        self.baudrate = dut_info["baudrate"]
        self.serial = None
        self._stop_event = threading.Event()

    def read(self, output_queue: Queue):
        """
        Read data from the TTTY device and put it into the output queue.

        Args:
            output_queue (Queue): The queue to put the read data into.
        """

        self._stop_event.clear()

        self.serial = serial.Serial(port=self.tty, baudrate=self.baudrate)
        self.buffer = bytearray()
        self.serial.flushInput()
        self.serial.flushOutput()

        while not self._stop_event.is_set():
            data = self.serial.read(self.serial.in_waiting)
            self.buffer.extend(data)
            self.process_buffer(output_queue)

    def process_buffer(self, output_queue):
        while True:
            if len(self.buffer) < 6:  # Minimum length for a valid frame
                break

            header = self.buffer[0:1]
            if not self.is_valid_header(header):
                self.buffer.pop(0)
                # TODO: add some sort of counter/logger for droped bytes
                continue

            if (
                len(self.buffer) < 3
            ):  # Need at least header, frame_id, and payload_length
                break

            payload_length = self.buffer[2]

            total_length = 1 + 1 + 1 + payload_length + 2 + 1
            if len(self.buffer) < total_length:
                break

            full_message = self.buffer[:total_length]

            tail = full_message[-1:]
            if not self.is_valid_tail(tail):
                self.buffer.pop(0)
                continue

            self.process_message(full_message, output_queue)
            self.buffer = self.buffer[total_length:]

    def is_valid_header(self, header):
        return header == b"\xaa"

    def is_valid_tail(self, tail):
        return tail == b"\x55"

    def process_message(self, message, output_queue):
        header = message[0:1]
        frame_id = message[1:2]
        payload_length = message[2]
        payload = message[3 : 3 + payload_length]
        crc_bytes = message[3 + payload_length : 3 + payload_length + 2]
        tail = message[-1:]

        packet = PacketFrame(header, frame_id, payload_length, payload, crc_bytes, tail)
        output_queue.put(packet)
