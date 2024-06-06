"""
Reboot machine functions. This is conceptually different from
the radiation_benchmarks setup. Here we use only private functions, and the only
public functions are reboot_machine turn_machine_on.
"""

import base64
import json
import subprocess
import time

import requests

from DUT_Tester.power_switch.error_codes import ErrorCodes

# Switches status, only used in this module
__ON = "ON"
__OFF = "OFF"

# Check if curl is available
try:
    subprocess.call(["curl", "--help"], stdout=subprocess.PIPE)
except OSError:
    raise OSError("CURL is not available, please install curl before using this module")


def _lindy_switch(
    status: str,
    switch_port: int,
    switch_ip: str,
    username="snmp",
    password="1234",
) -> ErrorCodes:
    """Lindy switch reboot rules
    :param status: ON or OFF
    :param switch_port: port to reboot
    :param switch_ip: ip address for the switch
    :param logger: logging.Logger obj
    :return: ErrorCodes enum
    """
    # before: led = f"{to_change[:(switch_port - 1)]}1{to_change[switch_port:]}"
    to_change = list("000000000000000000000000")
    to_change[switch_port - 1] = "1"
    led = "".join(to_change)
    if status == __ON:
        # TODO: Check if lindy switch accepts https protocol
        url = f"http://{switch_ip}/ons.cgi?led={led}"
    else:
        url = f"http://{switch_ip}/offs.cgi?led={led}"

    payload = {
        "led": led,
    }

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

    # print(url)
    # print(headers)
    default_string = "Could not change Lindy IP switch status, portNumber:"
    try:
        requests_status = requests.post(url, data=json.dumps(payload), headers=headers)
        requests_status.raise_for_status()
        reboot_status = ErrorCodes.SUCCESS
    except requests.exceptions.HTTPError as http_error:
        reboot_status = ErrorCodes.HTTP_ERROR
        # logger.consoleLogger.error(
        #     f"{default_string} {switch_port} status:{reboot_status} switchIP:{switch_ip} error:{http_error}"
        # )
    except requests.exceptions.ConnectionError as connection_error:
        reboot_status = ErrorCodes.CONNECTION_ERROR
        # logger.consoleLogger.error(
        #     f"{default_string} {switch_port} status:{reboot_status} switchIP:{switch_ip} error:{connection_error}"
        # )
    except requests.exceptions.Timeout as timeout_error:
        reboot_status = ErrorCodes.TIMEOUT_ERROR
        # logger.consoleLogger.error(
        #     f"{default_string} {switch_port} status:{reboot_status} switchIP:{switch_ip} error:{timeout_error}"
        # )
    except requests.exceptions.RequestException as general_error:
        reboot_status = ErrorCodes.GENERAL_ERROR
        # logger.consoleLogger.error(
        #     f"{default_string} {switch_port} status:{reboot_status} switchIP:{switch_ip} error:{general_error}"
        # )
    return reboot_status


def power_cycle(select_power_switch, power_IP):
    return_code = 0
    return_code = _lindy_switch("OFF", select_power_switch, power_IP)

    print("Powering down..", select_power_switch)

    time.sleep(10)

    return_code = _lindy_switch("ON", select_power_switch, power_IP)

    print("Powering up..", select_power_switch)

    time.sleep(10)

    return return_code
