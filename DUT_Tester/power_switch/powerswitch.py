from abc import ABC, abstractmethod
from error_codes import ErrorCodes


class PowerSwitch(ABC):
    """ Abstract base class for power switches.

    This class serves as an interface definition and is intended to be inhereted by an
    implementation of a certain type of power switch. Only one method is required to
    be implemented.

    Methods
    -------
    power_cycle(device, delay): ErrorCodes
        Powercycle specified device with a delay between off/on.

    """

    @abstractmethod
    def power_cycle(device: int, delay: int) -> ErrorCodes:
        """Power cycle on device/outlet/port of an powerswitch.

        Parameters
        ----------
        device : int
            Port or outlet to power cycle.
        delay : int
            Time in seconds to wait between power off and power on.

        Returns
        -------
        status : ErrorCodes
        """
        pass


import time
import base64
import json
import requests
from error_codes import ErrorCodes


class PSLindy(PowerSwitch):
    """Power switch class for controlling a Lindy power switch.

    Attributes
    ----------
    _ip: str
        IP-address of device
    _username: str
        Login user name
    _password: str
        Login password

    Methods
    -------
    power_cycle(device, delay): ErrorCodes
        Powercycle specified device with a delay between off/on.

    """
    __ON = "ON"
    __OFF = "OFF"

    def __init__(self, ip: str, username: str, password: str):
        self._ip = ip
        self._username = username
        self._password = password

    def _set_output(self, device: int, state: str) -> ErrorCodes:
        to_change = list("000000000000000000000000")
        to_change[device - 1] = "1"
        led = "".join(to_change)
        if state == self.__ON:
            # TODO: Check if lindy switch accepts https protocol
            url = f"http://{self._ip}/ons.cgi?led={led}"
        else:
            url = f"http://{self._ip}/offs.cgi?led={led}"

        payload = {
            "led": led,
        }

        str_token = f"{self._username}:{self._password}"
        base64_token = base64.b64encode(str_token.encode("ascii")).decode("ascii")

        headers = {
            "Host": self._ip,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:56.0) \
                    Gecko/20100101 Firefox/56.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Referer": f"http://{self._ip}/outlet.htm",
            "Authorization": f"Basic {base64_token}",
            "Connection": "keep-alive",
            "Content-Length": "0",
        }

        try:
            requests_status = requests.post(url,
                                            data=json.dumps(payload),
                                            headers=headers)
            requests_status.raise_for_status()
        except requests.exceptions.HTTPError:
            return ErrorCodes.HTTP_ERROR
        except requests.exceptions.ConnectionError:
            return ErrorCodes.CONNECTION_ERROR
        except requests.exceptions.Timeout:
            return ErrorCodes.TIMEOUT_ERROR
        except requests.exceptions.RequestException:
            return ErrorCodes.GENERAL_ERROR
        return ErrorCodes.SUCCESS

    def power_cycle(self, device: int, delay: int) -> ErrorCodes:
        ret = ErrorCodes.SUCCESS
        while ret == ErrorCodes.SUCCESS:
            ret = self._set_output(device, self.__OFF)
            time.sleep(delay)
            ret = self._set_output(device, self.__ON)
            time.sleep(delay)
        return ret
