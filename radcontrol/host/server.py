import threading
import select
import sys
from time import sleep
from devices.dut import DUT
from radcontrol.utils.logger import Logger
from radcontrol.power_switch.powerswitch import PowerSwitchController
from file_manager import (
    open_tmux_window,
    remove_tmux_window,
    add_tmux_window,
    get_dut_info,
)


class Server:
    def __init__(self, args):
        """
        Initialize the Server instance.

        Args:
            args: Parsed arguments containing configuration information.
        """
        self.args = args
        # self.uart_info = self.args.uart_info
        self.uart_info = get_dut_info("dut_config.yaml")

        self.dut_instances = {}  # Maps DUT names to DUT instances
        self.threads = {}  # Maps DUT names to their threads

        self.server_logger = Logger(mode="Server", verbose=3)

        self.print_arguments()
        self.power_controller = PowerSwitchController()

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
            # self.server_logger.consoleLogger.info(f"{arg}: {value}")

    def create_dut(self):
        """
        Create and initialize DUT instances based on the provided UART information.
        """
        try:
            for dut_info in self.uart_info.get("duts", []):
                dut_name = dut_info.get("name")
                if dut_name not in self.dut_instances:
                    self.initialize_and_start_dut(dut_name, dut_info)
                    self.server_logger.consoleLogger.info(
                        f"Added and initialized DUT with info: {dut_info}"
                    )
                else:
                    self.server_logger.consoleLogger.info(
                        f"DUT already added: {dut_info}"
                    )
        except Exception as e:
            self.server_logger.consoleLogger.error(
                f"Error creating DUT, connection error: {e}"
            )

    def start(self):
        """
        Start monitoring DUTs in separate threads and manage their lifecycle.
        """

        open_tmux_window()
        self.create_dut()
        self.stop_event = threading.Event()

        try:
            self.monitor_events()
        finally:
            self.stop()

    # def initialize_duts(self):
    #     """
    #     Initialize DUTs by powering them up and starting their monitoring threads.
    #     """
    #     for dut_name, dut_instance in self.dut_instances.items():
    #         self.power_cycle_dut(dut_instance)
    #         self.start_monitoring_thread(dut_name, dut_instance)

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

    def start_monitoring_thread(self, dut_name, dut_instance):
        """
        Start a monitoring thread for a DUT and add it to the list of threads.
        """
        thread = threading.Thread(target=dut_instance.monitor, daemon=True)
        self.threads[dut_name] = thread
        thread.start()

    def monitor_events(self):
        """
        Monitor the threads and restart them if they are not alive.
        """

        options = {
            "1": self.refresh_device_table,
            "2": self.power_cycle_device,
            "3": self.print_status,
        }

        sys.stdout.write("Enter option [1-3]: ")
        sys.stdout.flush()
        while not self.stop_event.is_set():

            # Check for user input
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                user_input = sys.stdin.readline().strip()
                if user_input in options:
                    options[user_input]()  # Execute the corresponding function
                else:
                    self.server_logger.consoleLogger.info(
                        f"Invalid option selected: {user_input}"
                    )
                sys.stdout.write("Enter option [1-3]: ")
                sys.stdout.flush()

            for dut_name, thread in self.threads.items():
                if not thread.is_alive():
                    self.restart_dut_monitoring_thread(dut_name)
            sleep(1)

    def initialize_and_start_dut(self, dut_name, dut_info):
        """
        Create a DUT instance, add it to the server, power it up, start its monitoring thread, and set up monitoring.
        """
        self.server_logger.consoleLogger.info(f"Initializing DUT: {dut_name}")

        # Create a new DUT instance
        dut_instance = DUT(dut_info, self.power_controller)
        self.dut_instances[dut_name] = dut_instance

        # Power cycle the DUT before starting monitoring
        self.power_cycle_dut(dut_instance)
        self.start_monitoring_thread(dut_name, dut_instance)

        # Set up tmux window for monitoring (if required)
        log_file_name = "/tmp/logger_" + dut_name
        add_tmux_window("monitor", dut_name, f"cat {log_file_name}")

    def refresh_device_table(self):
        self.server_logger.consoleLogger.info("Refreshing DUTs...")
        # Load the updated UART info from the configuration file
        self.uart_info = get_dut_info("dut_config.yaml")

        # Extract the new set of DUT names from the updated configuration
        new_dut_infos = self.uart_info.get("duts", [])
        new_dut_names = set(dut_info.get("name") for dut_info in new_dut_infos)

        # Get the current set of DUT names
        current_dut_names = set(self.dut_instances.keys())

        # Identify DUTs to remove and add
        duts_to_remove = current_dut_names - new_dut_names
        duts_to_add = new_dut_names - current_dut_names

        if duts_to_remove:
            self.server_logger.consoleLogger.info(f"DUTs to remove: {duts_to_remove}")
        if duts_to_add:
            self.server_logger.consoleLogger.info(f"DUTs to add: {duts_to_add}")

        # Remove DUTs that are no longer in the configuration
        for dut_name in duts_to_remove:
            self.remove_dut(dut_name)

        # Add new DUTs that are in the configuration but not currently active
        for dut_info in new_dut_infos:
            dut_name = dut_info.get("name")
            if dut_name in duts_to_add:
                self.add_new_dut(dut_name, dut_info)
            else:
                # Optionally, update existing DUT configurations if they have changed
                self.update_existing_dut(dut_name, dut_info)

    def power_cycle_device(self):
        self.server_logger.consoleLogger.info("Power Cycling")
        sys.stdout.write("Select DUT by name: ")
        sys.stdout.flush()
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            dut_name = sys.stdin.readline().strip()
            if dut_name in self.dut_instances:
                self.restart_dut_monitoring_thread(dut_name)
            else:
                self.server_logger.consoleLogger.info(
                    f"Invalid DUT selected: {dut_name}"
                )

    def print_status(self):
        self.server_logger.consoleLogger.info("Active DUTs:")
        for dut_name in self.dut_instances:
            self.server_logger.consoleLogger.info(f"DUT Name: {dut_name}")

    def restart_dut_monitoring_thread(self, dut_name):
        """
        Restart a monitoring thread for a DUT that is not alive.
        """
        dut_instance = self.dut_instances[dut_name]
        self.server_logger.consoleLogger.warning(
            f"Thread for DUT {dut_name} is not alive. Restarting..."
        )
        self.power_cycle_dut(dut_instance)
        new_thread = threading.Thread(target=dut_instance.monitor, daemon=True)
        dut_instance._stop_event = threading.Event()
        self.threads[dut_name] = new_thread
        new_thread.start()

    def stop(self):
        """
        Signal the main loop to stop, shut down the power controller, and clean up threads.
        """
        self.stop_event.set()
        self.power_controller.shutdown()

        # Stop and clean up all DUTs
        for dut_name in list(self.dut_instances.keys()):
            self.remove_dut(dut_name)

    def remove_dut(self, dut_name):
        """
        Remove a DUT from the server by stopping its monitoring thread and deleting its instance.
        """
        self.server_logger.consoleLogger.info(f"Removing DUT: {dut_name}")

        # Stop the DUT's monitoring thread
        dut_instance = self.dut_instances[dut_name]
        dut_instance.stop()  # Ensure the DUT's monitor method can exit
        thread = self.threads[dut_name]
        if thread.is_alive():
            thread.join(timeout=1)  # Wait for the thread to finish

        # Remove DUT from dictionaries
        del self.dut_instances[dut_name]
        del self.threads[dut_name]

        remove_tmux_window("monitor", dut_name)

    def add_new_dut(self, dut_name, dut_info):
        """
        Add and initialize a new DUT to the server.
        """
        self.server_logger.consoleLogger.info(f"Adding new DUT: {dut_name}")
        self.initialize_and_start_dut(dut_name, dut_info)

    # UNTESTED
    def update_existing_dut(self, dut_name, new_dut_info):
        """
        Update the configuration of an existing DUT if necessary.
        """
        dut_instance = self.dut_instances[dut_name]
        if dut_instance.config != new_dut_info:
            self.server_logger.consoleLogger.info(
                f"Updating configuration for DUT: {dut_name}"
            )
            # Update the DUT's configuration
            # dut_instance.update_config(new_dut_info)
            # Optionally, restart the monitoring thread if required
            self.restart_dut_monitoring_thread(dut_name)
