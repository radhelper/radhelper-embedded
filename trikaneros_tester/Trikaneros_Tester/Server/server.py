import os
import signal
import subprocess
import traceback
import time
from threading import Event

import requests
from requests.auth import HTTPBasicAuth

from Trikaneros_Tester.log_id import SERVER_POWERCYCLE_RPI, SERVER_POWERCYCLE_RPI_FAILED
from Trikaneros_Tester.power_switch.powerswitch import power_cycle
from Trikaneros_Tester.Server.log_monitor import LogMonitor
from Trikaneros_Tester.util import Logger


class Server():

    def __init__(self, args = None):
        self.event_stop = Event()

        self.log_folder = args.log_folder
        self.ip_address = args.ip_address
        self.port = args.port
        self.user = args.user
        self.switch_id = args.switch_id
        self.switch_ip = args.switch_ip
        self.client_ip = args.client_ip
        self.fallback_power_switch = args.fallback_power_switch
        self.no_power_cycle = args.no_power_cycle
        self.switch_password = args.switch_password
        self.switch_username = args.switch_username
        self.timeout = args.timeout
        self.dir = args.directory
        self.log_fetch_interval = args.log_fetch_interval

        self.last_fetch = time.time()

        self.logger = Logger('Server', self.log_folder, self.ip_address, self.port, verbose = args.verbose)

        self.log_monitor = LogMonitor(self.logger, self.event_stop)

    def start(self):
        signal.signal(signal.SIGINT, self.handler)

        self.log_monitor.start()

        # self.power_cycle_pi()
        # self.logger.socketReceiver.last_message = time.time()

        while True:
            if not self.no_power_cycle:
                if time.time() - self.logger.socketReceiver.last_message > self.timeout:
                    self.power_cycle_pi()
                    self.logger.socketReceiver.last_message = time.time()

            if time.time() - self.last_fetch > self.log_fetch_interval * 60:
                self.copy_logs()
                self.last_fetch = time.time()

            # WIESEP: Hack ping the raspberry pi due to arp issues
            self.ping_ip(self.client_ip)
            for ip_address, _ in (self.logger.socketReceiver.clients):
                self.ping_ip(ip_address)

            time.sleep(1)

    def ping_ip(self, ip_address):
        try:
            self.logger.consoleLogger.debug("Ping {}".format(ip_address))
            ret = subprocess.check_output(["ping", "-c", "1", ip_address], timeout = 5)
            if ret.decode('utf-8').find("1 received") == -1:
                self.logger.consoleLogger.warn("Failed to ping {}".format(ip_address))
        except:
            pass

    def copy_logs(self):
        client_path = self.dir

        for ip_address, _ in self.logger.socketReceiver.clients:
            server_path = os.path.join(self.log_folder, "clients", str(ip_address))
            os.makedirs(server_path, exist_ok = True)
            self.logger.consoleLogger.info("Fetching logs from {}@{}:{} to {}".format(
                self.user, ip_address, client_path, server_path))
            process = subprocess.Popen([
                "rsync", "-e", "ssh -o StrictHostKeyChecking=no", "-tr",
                "{}@{}:{}".format(self.user, ip_address, client_path), server_path
            ])
            process.wait()

    def power_cycle_pi(self):
        self.logger.consoleLogger.warn("Restarting Raspberry Pi...")
        self.logger.dataLogger.warn({
            'type': 'Server',
            'id': SERVER_POWERCYCLE_RPI,
            'timestamp': time.time(),
            'event': f'Communication Timeout. Restart Raspberry Pi.'
        })

        # TODO: Adjust to local setup
        try:
            if self.fallback_power_switch:
                url = f"http://{self.switch_ip}/control_outlet.htm?outlet{self.switch_id}=1&op=2&submit=Apply"
                ret = requests.get(url, auth = HTTPBasicAuth(self.switch_username, self.switch_password), timeout = 5)
                self.logger.consoleLogger.debug(f"Calling {url}")
                if ret.status_code != 200:
                    self.logger.consoleLogger.warn("Failed to restart Raspberry Pi")
                    self.logger.consoleLogger.warn(f"Got {ret.status_code}")

                    self.logger.dataLogger.warn({
                        'type': 'Server',
                        'id': SERVER_POWERCYCLE_RPI_FAILED,
                        'timestamp': time.time(),
                        'event': f'Failed to restart Raspberry Pi.'
                    })
            else:
                power_cycle(self.switch_id, self.switch_ip, self.logger.consoleLogger, self.switch_username,
                            self.switch_password)
        except:
            traceback.print_exc()
            self.logger.consoleLogger.warn("Failed to restart Raspberry Pi")
            pass

    def stop(self):
        self.logger.consoleLogger.warn("Stopping server...")
        self.event_stop.set()
        self.logger.socketReceiver.abort = 1
        exit(0)

    def handler(self, signum, frame):
        self.stop()
