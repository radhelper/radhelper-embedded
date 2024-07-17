import threading
from time import sleep
from devices.dut import DUT
from utils.util import Logger
from radcontrol.power_switch.powerswitch import PowerSwitchController


class Server:
    def __init__(self, args):
        """
        Initialize the Server instance.

        Args:
            args: Parsed arguments containing configuration information.
        """
        self.args = args
        self.duts = []

        self.server_logger = Logger(mode="Server", verbose=3)

        self.print_arguments()
        self.power_controller = PowerSwitchController()

        self.create_dut()
        self.stop_event = threading.Event()

        self.start()

    def print_arguments(self):
        """
        Print the arguments with which the server is started.
        """
        self.server_logger.consoleLogger.info(
            f"Starting server with the following arguments:"
        )
        for arg, value in vars(self.args).items():
            self.server_logger.dataLogger.info(f"{arg}: {value}")
            self.server_logger.consoleLogger.info(f"{arg}: {value}")

    def create_dut(self):
        """
        Create DUT instances based on the provided UART information in the arguments.
        Handles the initialization and appending of DUT instances to the server.
        """
        try:
            for dut in self.args.uart_info.get("duts", []):
                dut_instance = DUT(dut, self.power_controller)
                self.duts.append(dut_instance)
        except Exception as e:
            self.server_logger.consoleLogger.error(
                f"Error creating DUT, connection error: {e}"
            )

    def start(self):
        """
        Start monitoring DUTs in separate threads and manage their lifecycle.
        """
        self.threads = []
        self.initialize_duts()

        try:
            self.monitor_threads()
        finally:
            self.stop()

    def initialize_duts(self):
        """
        Initialize DUTs by powering them up and starting their monitoring threads.
        """
        for dut in self.duts:
            self.power_cycle_dut(dut)
            self.start_monitoring_thread(dut)

    def power_cycle_dut(self, dut):
        """
        Power cycle a DUT and wait for the process to complete.
        """
        event = threading.Event()
        dut.power_controller.queue_power_cycle(
            dut.power_switch_port,
            dut.power_port_IP,
            event,
            dut.reboot_interval,
        )
        event.wait()

    def start_monitoring_thread(self, dut):
        """
        Start a monitoring thread for a DUT and add it to the list of threads.
        """
        thread = threading.Thread(target=dut.monitor, daemon=True)
        self.threads.append((dut, thread))
        thread.start()

    def monitor_threads(self):
        """
        Monitor the threads and restart them if they are not alive.
        """
        while not self.stop_event.is_set():
            for i, (dut, thread) in enumerate(self.threads):
                if not thread.is_alive():
                    self.restart_dut_monitoring_thread(dut, i)
            sleep(1)

    def restart_dut_monitoring_thread(self, dut, index):
        """
        Restart a monitoring thread for a DUT that is not alive.
        """

        self.server_logger.consoleLogger.warning(
            f"Thread for DUT {dut.name} is not alive. Restarting..."
        )
        self.power_cycle_dut(dut)
        new_thread = threading.Thread(target=dut.monitor, daemon=True)
        dut._stop_event = threading.Event()
        self.threads[index] = (dut, new_thread)
        new_thread.start()

    def stop(self):
        """
        Signal the main loop to stop, shut down the power controller, and clean up threads.
        """
        self.stop_event.set()
        self.power_controller.shutdown()

        # Properly handle stopping the server and cleaning up threads
        for dut in self.duts:
            dut.stop()  # Ensure DUT stops its thread

        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1)
