import base64
import json
import subprocess
import time
import threading
import queue
import requests
from radcontrol.power_switch.error_codes import ErrorCodes
from radcontrol.utils.logger import Logger


class PowerSwitchController:
    __ON = "ON"
    __OFF = "OFF"

    def __init__(self):
        """
        Initialize the PowerSwitchController instance.

        Raises:
            OSError: If CURL is not available.
        """
        # Check if curl is available
        try:
            subprocess.call(["curl", "--help"], stdout=subprocess.PIPE)
        except OSError:
            raise OSError(
                "CURL is not available, please install curl before using this module"
            )

        self.power_switch_logger = Logger(mode="PowerS", verbose=3)
        self.command_queue = queue.Queue()
        self.switch_thread = threading.Thread(target=self._process_commands)
        self.switch_thread.start()

    def _lindy_switch(
        self,
        status: str,
        switch_port: int,
        switch_ip: str,
        username="snmp",
        password="1234",
    ) -> ErrorCodes:
        """
        Change the status of a Lindy IP switch.

        Args:
            status (str): The desired switch status ("ON" or "OFF").
            switch_port (int): The port number of the switch to change.
            switch_ip (str): The IP address of the switch.
            username (str): The username for switch authentication.
            password (str): The password for switch authentication.

        Returns:
            ErrorCodes: The status code indicating the result of the operation.
        """
        switch_status_list = list("000000000000000000000000")
        switch_status_list[switch_port - 1] = "1"
        led = "".join(switch_status_list)
        url = (
            f"http://{switch_ip}/ons.cgi?led={led}"
            if status == self.__ON
            else f"http://{switch_ip}/offs.cgi?led={led}"
        )
        payload = {"led": led}
        str_token = f"{username}:{password}"
        base64_token = base64.b64encode(str_token.encode("ascii")).decode("ascii")

        headers = {
            "Host": switch_ip,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:56.0) Gecko/20100101 Firefox/56.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Referer": f"http://{switch_ip}/outlet.htm",
            "Authorization": f"Basic {base64_token}",
            "Connection": "keep-alive",
            "Content-Length": "0",
        }

        default_string = "Could not change Lindy IP switch status, portNumber:"
        try:
            requests_status = requests.post(
                url, data=json.dumps(payload), headers=headers
            )
            requests_status.raise_for_status()
            reboot_status = ErrorCodes.SUCCESS
        except requests.exceptions.HTTPError as http_error:
            reboot_status = ErrorCodes.HTTP_ERROR
        except requests.exceptions.ConnectionError as connection_error:
            reboot_status = ErrorCodes.CONNECTION_ERROR
        except requests.exceptions.Timeout as timeout_error:
            reboot_status = ErrorCodes.TIMEOUT_ERROR
        except requests.exceptions.RequestException as general_error:
            reboot_status = ErrorCodes.GENERAL_ERROR
        return reboot_status

    def power_cycle(self, select_power_switch, power_IP, event, interval=10):
        """
        Perform a power cycle on the specified power switch.

        Args:
            select_power_switch (int): The port number of the switch to power cycle.
            power_IP (str): The IP address of the power switch.
            event (threading.Event): Event to signal completion.
            interval (int): Time to wait between power off and power on.

        Returns:
            ErrorCodes: The status code indicating the result of the operation.
        """
        return_code = self._lindy_switch(self.__OFF, select_power_switch, power_IP)
        self.power_switch_logger.consoleLogger.warning(
            f"Powering down {select_power_switch}"
        )
        time.sleep(interval)
        return_code = self._lindy_switch(self.__ON, select_power_switch, power_IP)
        self.power_switch_logger.consoleLogger.warning(
            f"Powering up {select_power_switch}"
        )
        time.sleep(interval)
        event.set()
        return return_code

    def _process_commands(self):
        """
        Process commands from the command queue to power cycle devices.
        """
        while True:
            command = self.command_queue.get()
            if command is None:  # Exit signal
                break
            self.power_cycle(*command)
            self.command_queue.task_done()

    def queue_power_cycle(self, select_power_switch, power_IP, event, interval):
        """
        Queue a power cycle command for a specified power switch.

        Args:
            select_power_switch (int): The port number of the switch to power cycle.
            power_IP (str): The IP address of the power switch.
            event (threading.Event): Event to signal completion.
            interval (int): Time to wait between power off and power on.
        """
        self.command_queue.put((select_power_switch, power_IP, event, interval))

    def shutdown(self):
        """
        Shut down the power switch controller, stopping the command processing thread.
        """
        self.command_queue.put(None)
        self.switch_thread.join()
