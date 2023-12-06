import os
import shutil
import signal
import time
from threading import Event

from DUT_Tester.Client.uart_monitor import UARTMonitor
from DUT_Tester.log_id import CLIENT_ERROR
from DUT_Tester.util import Logger

import DUT_Tester.global_vars as global_vars


class Client:
    def __init__(self, args=None):
        self.event_stop = Event()

        self.event_flash = Event()

        self.args = args

        self.log_folder = args.log_folder
        self.ip_address = args.ip_address
        self.port = args.port
        self.verbose = args.verbose
        self.verbose = args.verbose

        self.data_monitor_alive = True

        self.freq_monitor_data = args.freq_monitor_data

        self.uart_monitors = []
        self.loggers = []

        self.general_logger = Logger(
            "Client",
            self.log_folder,
            self.ip_address,
            self.port,
            verbose=self.verbose,
            name_specifier="general_logger",
            log_rotate_interval=args.log_rotate_interval,
        )
        self.loggers.append(self.general_logger)

        # global_vars.uart_info
        uarts = global_vars.uart_info
        i = 0
        for uart in uarts["uart"]:
            if i >= uarts["number_conected_uarts"]:
                break

            setattr(self, "event_" + uart["name"] + "_monitor_heartbeat", Event())
            print("event_" + uart["name"] + "_monitor_heartbeat")

            uart_monitor_name = uart["name"] + "_monitor"
            uart_logger = Logger(
                "Client",
                self.log_folder,
                self.ip_address,
                self.port,
                verbose=self.verbose,
                name_specifier=uart_monitor_name,
                log_rotate_interval=args.log_rotate_interval,
            )
            self.loggers.append(uart_logger)
            attr_value = UARTMonitor(
                logger=uart_logger,
                event_heartbeat=getattr(
                    self, "event_" + uart["name"] + "_monitor_heartbeat"
                ),
                event_stop=self.event_stop,
                name=uart_monitor_name,
                freq=self.freq_monitor_data,
                tty=uart["tty"],
                baudrate=uart["baudrate"],
                lindy_switch=uart["lindy_switch"],
                lindy_port=uart["lindy_port"],
            )

            setattr(self, uart_monitor_name, attr_value)
            self.uart_monitors.append(attr_value)

            i += 1

    def start(self):
        try:
            signal.signal(signal.SIGINT, self.handler)
            signal.signal(signal.SIGTERM, self.handler)

            for uart_monitor in self.uart_monitors:
                uart_monitor.start()

            self.general_logger.consoleLogger.info(f"Started Client. [{os.getpid()}]")

            while True:
                # Check all monitor threads
                self.check_monitors()

                # Check if disk space is running low and delete old log files if necessary
                # self.check_disk_space()

                # Do this check every second
                time.sleep(1)

        except Exception as e:
            for logger in self.loggers:
                logger.consoleLogger.error(f"Error: {str(e)}")
                logger.dataLogger.info(
                    {
                        "type": "Client",
                        "id": CLIENT_ERROR,
                        "timestamp": time.time(),
                        "event": f"Client error: {str(e)}",
                    }
                )

        self.fail()

    def check_monitors(self):
        for uart_monitor in self.uart_monitors:
            # Check if  monitor thread is still alive
            # if not self.event_uart0_monitor_heartbeat.is_set() and self.data_monitor_alive:
            if not uart_monitor.event_heartbeat.is_set() and self.data_monitor_alive:
                self.data_monitor_alive = False
                uart_monitor.logger.dataLogger.info(
                    {
                        "type": "Client",
                        "id": CLIENT_ERROR,
                        "timestamp": time.time(),
                        "event": "Data Monitor thread seems not to be alive.",
                    }
                )
                self.general_logger.consoleLogger.error(
                    f"Data Monitor thread for {uart_monitor.name} seems not to be alive."
                )
                self.fail()
            uart_monitor.event_heartbeat.clear()

    def check_disk_space(self):
        stat = shutil.disk_usage(self.log_folder)

        # Less than 100MB free space
        if stat.free < 100e6:
            self.general_logger.consoleLogger.warn(
                f"Less than 100MB free space left on disk. Deleting old log file..."
            )
            # Delete oldest log file
            files = os.listdir(self.log_folder)
            files.sort(key=os.path.getmtime)
            os.remove(os.path.join(self.log_folder, files[0]))

    def stop(self):
        self.general_logger.consoleLogger.warn("Stopping client...")
        self.event_stop.set()

        for uart_monitor in self.uart_monitors:
            uart_monitor.join()

        exit(0)

    def fail(self):
        self.general_logger.consoleLogger.warn(
            "Exiting client wiht error (systemd will restart)..."
        )
        self.event_stop.set()

        exit(1)

    def handler(self, signum, frame):
        self.stop()
