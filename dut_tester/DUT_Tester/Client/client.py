import os
import shutil
import signal
import time
from threading import Event

from Trikaneros_Tester.Client.uart_monitor import UARTMonitor
from Trikaneros_Tester.log_id import CLIENT_ERROR
from Trikaneros_Tester.util import Logger


class Client():

    def __init__(self, args = None):
        self.event_stop = Event()

        self.event_flash = Event()

        self.args = args

        self.log_folder = args.log_folder
        self.ip_address = args.ip_address
        self.port = args.port
        self.verbose = args.verbose
        self.verbose = args.verbose

        self.event_uart0_monitor_heartbeat = Event()
        self.data_monitor_alive = True

        self.freq_monitor_data = args.freq_monitor_data

        self.logger = Logger('Client',
                             self.log_folder,
                             self.ip_address,
                             self.port,
                             verbose = self.verbose,
                             log_rotate_interval = args.log_rotate_interval)

        self.uart0_monitor = UARTMonitor(self.logger,
                                         self.event_uart0_monitor_heartbeat,
                                         self.event_stop,
                                         freq = self.freq_monitor_data,
                                         tty = "/dev/serial0",
                                         baudrate = 115200)

    def start(self):
        try:
            signal.signal(signal.SIGINT, self.handler)
            signal.signal(signal.SIGTERM, self.handler)

            self.uart0_monitor.start()

            self.logger.consoleLogger.info(f'Started Client. [{os.getpid()}]')

            while True:
                # Check all monitor threads
                self.check_monitors()

                # Check if disk space is running low and delete old log files if necessary
                self.check_disk_space()

                # Do this check every second
                time.sleep(1)

        except Exception as e:
            self.logger.consoleLogger.error(f"Error: {str(e)}")
            self.logger.dataLogger.info({
                'type': 'Client',
                'id': CLIENT_ERROR,
                'timestamp': time.time(),
                'event': f'Client error: {str(e)}'
            })

        self.fail()

    def check_monitors(self):
        # Check if uart0 monitor thread is still alive
        if not self.event_uart0_monitor_heartbeat.is_set() and self.data_monitor_alive:
            self.data_monitor_alive = False
            self.logger.dataLogger.info({
                'type': 'Client',
                'id': CLIENT_ERROR,
                'timestamp': time.time(),
                'event': 'Data Monitor thread seems not to be alive.'
            })
            self.logger.consoleLogger.error("Data Monitor thread seems not to be alive.")
            self.fail()

        self.event_uart0_monitor_heartbeat.clear()

    def check_disk_space(self):
        stat = shutil.disk_usage(self.log_folder)

        # Less than 100MB free space
        if stat.free < 100E6:
            self.logger.consoleLogger.warn(f"Less than 100MB free space left on disk. Deleting old log file...")
            # Delete oldest log file
            files = os.listdir(self.log_folder)
            files.sort(key = os.path.getmtime)
            os.remove(os.path.join(self.log_folder, files[0]))

    def stop(self):
        self.logger.consoleLogger.warn("Stopping client...")
        self.event_stop.set()

        self.uart0_monitor.join()
        exit(0)

    def fail(self):
        self.logger.consoleLogger.warn("Exiting client wiht error (systemd will restart)...")
        self.event_stop.set()

        exit(1)

    def handler(self, signum, frame):
        self.stop()
