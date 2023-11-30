"""
Reboot machine functions. This is conceptually different from
the radiation_benchmarks setup. Here we use only private functions, and the only
public functions are reboot_machine turn_machine_on.
"""

import base64
import json
import logging
import os
import re
import subprocess
import threading
import time
import typing

import requests

from Trikaneros_Tester.power_switch.error_codes import ErrorCodes

# Switches status, only used in this module
__ON = "ON"
__OFF = "OFF"

# Make sure that everything here is thread safe
__GLOBAL_LOCK = threading.Lock()

# Check if curl is available
try:
    subprocess.call(["curl", "--help"], stdout = subprocess.PIPE)
except OSError:
    raise OSError("CURL is not available, please install curl before using this module")


def _lindy_switch(status: str,
                  switch_port: int,
                  switch_ip: str,
                  logger: logging.Logger,
                  username = "snmp",
                  password = '1234') -> ErrorCodes:
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
    base64_token = base64.b64encode(str_token.encode('ascii')).decode('ascii')

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

    print(url)
    print(headers)
    default_string = "Could not change Lindy IP switch status, portNumber:"
    try:
        requests_status = requests.post(url, data = json.dumps(payload), headers = headers)
        requests_status.raise_for_status()
        reboot_status = ErrorCodes.SUCCESS
    except requests.exceptions.HTTPError as http_error:
        reboot_status = ErrorCodes.HTTP_ERROR
        logger.error(f"{default_string} {switch_port} status:{reboot_status} switchIP:{switch_ip} error:{http_error}")
    except requests.exceptions.ConnectionError as connection_error:
        reboot_status = ErrorCodes.CONNECTION_ERROR
        logger.error(
            f"{default_string} {switch_port} status:{reboot_status} switchIP:{switch_ip} error:{connection_error}")
    except requests.exceptions.Timeout as timeout_error:
        reboot_status = ErrorCodes.TIMEOUT_ERROR
        logger.error(
            f"{default_string} {switch_port} status:{reboot_status} switchIP:{switch_ip} error:{timeout_error}")
    except requests.exceptions.RequestException as general_error:
        reboot_status = ErrorCodes.GENERAL_ERROR
        logger.error(
            f"{default_string} {switch_port} status:{reboot_status} switchIP:{switch_ip} error:{general_error}")
    return reboot_status


def _common_switch_command(status: str, switch_ip: str, switch_port: int) -> ErrorCodes:
    """Common switch reboot rules
    :param status: ON or OFF
    :param switch_ip: ip address for the switch
    :param switch_port: port to reboot
    :return: ErrorCodes enum
    """
    port_default_cmd = "pw%1dName=&P6%1d=%%s&P6%1d_TS=&P6%1d_TC=&" % (
        switch_port,
        switch_port - 1,
        switch_port - 1,
        switch_port - 1,
    )

    cmd = 'curl --data "'
    cmd += port_default_cmd % ("On" if status == __ON else "Off")
    cmd += '&Apply=Apply" '
    cmd += f"http://{switch_ip}/tgi/iocontrol.tgi -o /dev/null "
    # Execute the command
    tmp_file = "/tmp/server_error_execute_command"
    result = os.system(f"{cmd} 2>{tmp_file}")
    with open(tmp_file) as err:
        success_line = False
        for line in err:
            m = re.match(
                r"\d+ {2}\d+ {4}\d+ {2}\d+ {2}\d+ {4}\d+ {2}\d+ {4}\d+ --:--:-- --:--:-- --:--:-- \d+",
                line,
            )
            if m:
                success_line = True
        if success_line is False or result != 0:
            return ErrorCodes.GENERAL_ERROR
    return ErrorCodes.SUCCESS


def _select_command_on_switch(
    status: str,
    switch_model: str,
    switch_port: int,
    switch_ip: str,
    logger: logging.Logger,
) -> ErrorCodes:
    """Select the switch and execute the command
    :param status: ON or OFF
    :param switch_model: model of the switch. Supported now default and lindy
    :param switch_port: port to reboot
    :param switch_ip: ip address for the switch
    :param logger: logging.Logger obj
    :return: ErrorCodes enum, if the switch is not defined it will trow a ValueError exception
    """
    with __GLOBAL_LOCK:
        if switch_model == "default":
            return _common_switch_command(status, switch_ip, switch_port)
        elif switch_model == "lindy":
            return _lindy_switch(status, switch_port, switch_ip, logger)
        else:
            raise ValueError("Incorrect switch set to switch_model")


def reboot_machine(
    address: str,
    switch_model: str,
    switch_port: int,
    switch_ip: str,
    rebooting_sleep: float,
    logger_name: str,
    thread_event: threading.Event = None,
) -> typing.Tuple[ErrorCodes, ErrorCodes]:
    """Public function to reboot a machine
    :param address: Address of the machine that is being rebooted
    :param switch_model: model of the switch. Supported now default and lindy
    :param switch_port: port to reboot
    :param switch_ip: ip address for the switch
    :param rebooting_sleep: How many seconds the machine must be OFF before turn ON again
    :param logger_name: logger name defined in the main setup module
    :param thread_event: thread event to sleep the thread when multiple machine are being used
    :return: a tuple containing the outcomes of the OFF and ON commands
    """
    logger = logging.getLogger(f"{logger_name}.{__name__}")
    logger.info(f"Rebooting machine, IP:{address} switch_IP:{switch_ip} switch_port:{switch_port}")
    off_status = _select_command_on_switch(
        status = __OFF,
        switch_model = switch_model,
        switch_port = switch_port,
        switch_ip = switch_ip,
        logger = logger,
    )
    if thread_event:
        thread_event.wait(rebooting_sleep)
    else:
        time.sleep(rebooting_sleep)

    on_status = _select_command_on_switch(
        status = __ON,
        switch_model = switch_model,
        switch_port = switch_port,
        switch_ip = switch_ip,
        logger = logger,
    )
    return off_status, on_status


def turn_machine_on(address: str, switch_model: str, switch_port: int, switch_ip: str, logger_name: str) -> ErrorCodes:
    """Public function to turn ON a machine
    :param address: Address of the machine that is being turned ON
    :param switch_model: model of the switch. Supported now default and lindy
    :param switch_port: port to reboot
    :param switch_ip: ip address for the switch
    :param logger_name: logger name defined in the main setup module
    :return: ErrorCodes status
    """
    logger = logging.getLogger(f"{logger_name}.{__name__}")
    logger.info(f"Turning ON machine:{address} switch_IP:{switch_ip} switch_port:{switch_port}")
    return _select_command_on_switch(
        status = __ON,
        switch_model = switch_model,
        switch_port = switch_port,
        switch_ip = switch_ip,
        logger = logger,
    )


def turn_machine_off(address: str, switch_model: str, switch_port: int, switch_ip: str, logger_name: str) -> ErrorCodes:
    """Public function to turn OFF a machine
    :param address: Address of the machine that is being turned OFF
    :param switch_model: model of the switch. Supported now default and lindy
    :param switch_port: port to reboot
    :param switch_ip: ip address for the switch
    :param logger_name: logger name defined in the main setup module
    :return: ErrorCodes status
    """
    logger = logging.getLogger(f"{logger_name}.{__name__}")
    logger.info(f"Turning OFF machine:{address} switch_IP:{switch_ip} switch_port:{switch_port}")
    return _select_command_on_switch(
        status = __OFF,
        switch_model = switch_model,
        switch_port = switch_port,
        switch_ip = switch_ip,
        logger = logger,
    )


def power_cycle(select_power_switch, power_IP, logger, username = "snmp", password = '1234'):
    return_code = 0
    return_code = _lindy_switch("OFF", select_power_switch, power_IP, logger, username, password)
    logger.info(f"Powering down port {select_power_switch}...")
    time.sleep(20)
    return_code = _lindy_switch("ON", select_power_switch, power_IP, logger, username, password)
    logger.info(f"Powering up port {select_power_switch}...")
    time.sleep(20)
    return return_code
