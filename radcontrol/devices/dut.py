import threading
from queue import Queue, Empty
from utils.util import Logger
from host.log_id import DUT_QUEUE_EMPTY, DUT_QUEUE_NORMAL
from devices.strategies.tty_strategy import TTYStrategy
from devices.strategies.ip_strategy import IPStrategy
from frame.frame_decoder import PacketFrame

USB = "usb"
Ether = "ether"


class DUT:
    """
    Device Under Test (DUT) class for managing device communication and monitoring.
    """

    def __init__(self, dut, PowerSwitchController):
        """
        Initialize the DUT instance.

        Args:
            dut_info (dict): Dictionary containing DUT information.
            PowerSwitchController (PowerSwitchController): Instance of the power switch controller.
        """
        self.name = dut["name"]
        self.connection = dut["connection"]
        self.power_switch_port = dut["power_switch_port"]
        self.power_port_IP = dut["power_port_IP"]

        self.power_controller = PowerSwitchController

        self.reboot_interval = 1

        self.dut_logger = Logger(mode=self.name, verbose=3)

        if self.connection == USB:
            self._strategy = TTYStrategy(dut)
        elif self.connection == Ether:
            self._strategy = IPStrategy(dut)
        else:
            self.dut_logger.consoleLogger.error(
                f"Connection {self.connection} not recognized for DUT {self.name}"
            )

        self.read_thread = None
        self._stop_event = threading.Event()
        self.output_queue = Queue()

    def monitor(self):
        """
        Monitor the DUT by starting a read thread and handling power cycles.
        """

        self.read_thread = threading.Thread(target=self.perform_read, daemon=True)
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

    def perform_read(self):
        """
        Perform the read operation using the selected strategy.
        """
        return self._strategy.read(self.output_queue)

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
        Stop the DUT monitoring and clean up the thread.
        """
        self._stop_event.set()
        self._strategy._stop_event.set()
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=1)

    # def get_thread_id():
    #     """
    #     Fetch the thread ID using ctypes.

    #     Returns:
    #         int: The thread ID.
    #     """
    #     return ctypes.CDLL("libc.so.6").syscall(186)
