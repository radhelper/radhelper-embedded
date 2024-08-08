import threading
import serial
from queue import Queue, Empty
from utils.util import Logger
from host.log_id import DUT_QUEUE_EMPTY, DUT_QUEUE_NORMAL
from frame.frame_decoder import PacketFrame


class DUT:
    """
    Device Under Test (DUT) class for managing device communication and monitoring.
    """

    def __init__(self, dut, PowerSwitchController):
        """
        Initialize the DUT instance.

        Args:
            dut (dict): Dictionary containing DUT information.
            PowerSwitchController (PowerSwitchController): Instance of the power
            switch controller.
        """
        self.name = dut["name"]
        self.url = dut["url"]
        self.baudrate = dut["baudrate"]
        self.power_switch_port = dut["power_switch_port"]
        self.power_port_IP = dut["power_port_IP"]

        self.power_controller = PowerSwitchController
        self.reboot_interval = 1  # seconds between powercycle on power controller
        self.serial = None
        self.buffer = bytearray()

        self.dut_logger = Logger(mode=self.name, verbose=3)

        self.read_thread = None
        self._stop_event = threading.Event()
        self.output_queue = Queue()

    def read(self):
        """
        Read data from the serial device and put it into the output queue.
        """
        # Setup threadlock and serial interface
        self._stop_event.clear()
        self.serial = serial.serial_for_url(self.url, baudrate=self.baudrate)
        self.serial.flushInput()
        self.serial.flushOutput()

        while not self._stop_event.is_set():
            data = self.serial.read(self.serial.in_waiting)
            self.buffer.extend(data)
            self.process_buffer(self.output_queue)

        # Free up hardware interface for later connection
        self.serial.__del__()
        self.serial = None

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

    def monitor(self):
        """
        Monitor the DUT by starting a read thread and handling power cycles.
        """

        self.read_thread = threading.Thread(target=self.read, daemon=True)
        self.read_thread.start()

        self.dut_logger.dataLogger.warning(f"Monitor started")

        try:
            while not self._stop_event.is_set():
                data, error_code = self.get_data(timeout=2)  # Adjust timeout as needed
                if data:
                    self.dut_logger.consoleLogger.debug(
                        data.get_log_message(format_type="hex")
                    )
                    self.dut_logger.consoleLogger.debug(
                        data.get_log_message(format_type="decoded")
                    )
                    self.dut_logger.consoleLogger.debug(data.get_log_message())
                if error_code == DUT_QUEUE_NORMAL:
                    continue
                elif error_code == DUT_QUEUE_EMPTY:
                    self.dut_logger.consoleLogger.warning(f"error out somehow")
                    break

        finally:
            self.stop()  # seppuku

    def get_data(self, timeout=None):
        """
        Get data from the output queue with an optional timeout.

        Args:
            timeout (int, optional): Time to wait for data before raising Empty exception.

        Returns:
            tuple: Data read from the queue and error code.
        """
        try:
            data = self.output_queue.get(timeout=timeout)
            # This is where I parse the data package and check for transmission errors
            error_code = DUT_QUEUE_NORMAL  # Placeholder for actual error code parsing
            return data, error_code
        except Empty:
            return None, DUT_QUEUE_EMPTY

    def stop(self):
        """
        Stop the DUT monitoring, clean up the thread and serial device.
        """
        self._stop_event.set()
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=1)
        if self.serial:
            self.serial.__del__()
            self.serial = None

    # def get_thread_id():
    #     """
    #     Fetch the thread ID using ctypes.

    #     Returns:
    #         int: The thread ID.
    #     """
    #     return ctypes.CDLL("libc.so.6").syscall(186)
