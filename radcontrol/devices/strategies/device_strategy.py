from abc import ABC, abstractmethod
from queue import Queue

class DeviceStrategy(ABC):
    """
    Abstract base class for device communication strategies.
    """
    @abstractmethod
    def read(self, output_queue: Queue):
        """
        Read data from the device and put it into the output queue.

        Args:
            output_queue (Queue): The queue to put the read data into.
        """
        pass
