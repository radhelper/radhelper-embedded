from devices.strategies.device_strategy import DeviceStrategy
from queue import Queue
from time import sleep

class IPStrategy(DeviceStrategy):
    """
    Concrete strategy for IP address-based device communication.
    """
    def __init__(self, dut_info):
        """
        Initialize IPStrategy with DUT information.

        Args:
            dut_info (dict): Dictionary containing DUT information.
        """
        self.ip = dut_info["ip"]
        self.baudrate = dut_info["baudrate"]
        
    def read(self, output_queue: Queue):
        """
        Read data from the IP device and put it into the output queue.

        Args:
            output_queue (Queue): The queue to put the read data into.
        """
        while True:
            data = f"Data from {self.ip} with baudrate {self.baudrate}"
            output_queue.put(data)
            sleep(1)
