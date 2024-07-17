import binascii
import os
import time
from threading import Event, Thread

import serial

from DUT_Tester.log_id import (
    CLIENT_SERIAL_TIMEOUT,
    CLIENT_SERIAL_FRAME_RX,
    CLIENT_SERIAL_FRAME_ERROR,
)
from DUT_Tester.util import Logger

from DUT_Tester.crc_table import crcTable

from DUT_Tester.power_switch.error_codes import ErrorCodes
import DUT_Tester.power_switch.powerswitch as ps
from DUT_Tester.Client.payload_decoding import parse_payload

SERIAL_TIMEOUT = 15
MIN_FRAME_INTERVAL = 2
SLEEP_AFTER_REBOOT = 20


class UARTMonitor(Thread):
    def __init__(
        self,
        logger: Logger,
        event_heartbeat: Event,
        event_stop: Event,
        name="",
        freq=100,
        tty="/dev/ttyUSB0",
        baudrate=115200,
        lindy_switch="192.168.1.240",
        lindy_port=1,
    ):
        Thread.__init__(self)
        self.deamon = True
        self.event_heartbeat = event_heartbeat
        self.event_stop = event_stop
        self.baudrate = baudrate
        self.tty = tty
        self.name = name
        self.lindy_switch = lindy_switch
        self.lindy_port = lindy_port

        self.max_buffer_size = 524  ## Equals to 2 maxed frames
        self.frame_package_size = 6

        self.freq = freq
        self.logger = logger

        self.reboot_start_time = time.time() - 10

        # self.DUT_rebooting = False

        self.serial = None

        self.last_read_time = time.time()
        self.last_frame_time = time.time()

        self.serial_timeout = False
        self.device_is_off = True

    def run(self):
        self.event_heartbeat.set()

        self.logger.consoleLogger.info(
            f'Started UART "{self.name}" Monitor Thread. [{os.getpid()}]'
        )

        self.serial = serial.Serial(port=self.tty, baudrate=self.baudrate)

        self.serial.flushInput()
        self.serial.flushOutput()

        self.power_up_DUT(self.lindy_port, self.lindy_switch)

        while not self.event_stop.is_set():
            # Set heartbeat signal
            self.event_heartbeat.set()

            frame_buffer = (
                self.read_frame_from_serial()
            )  # This function is blocking for at least SERIAL_TIMEOUT and at max SERIAL_TIMEOUT

            if frame_buffer is not None:
                try:
                    frame_buffer_hex = frame_buffer.decode("utf-8")
                except:
                    frame_buffer_hex = str(binascii.hexlify(frame_buffer), "ascii")

                # don't log unless is a complete frame or abandoned frame
                self.logger.dataLogger.info(
                    {
                        "type": "Serial " + self.name,
                        "id": CLIENT_SERIAL_FRAME_RX,
                        "timestamp": time.time(),
                        "data": frame_buffer_hex,
                    }
                )
                self.logger.consoleLogger.info(
                    "[Serial] " + self.name + " " + frame_buffer_hex.rstrip("\n")
                )
                #### process the received loop and check for frames
                # would be good to at least check for double frames...
                # self.check_for_frame(frame_buffer)

            else:  ## If its not getting anything, try powering up
                self.power_up_DUT(self.lindy_port, self.lindy_switch)

        # self.PI.serial_close(self.serial)
        self.serial.close()
        self.logger.consoleLogger.info(f"Stopped Data Monitor Thread. [{os.getpid()}]")

    ##### loop to listen to port
    # does not quit until the serial port goes quiet for a while
    # timeout if nothing gets sent for a while
    # max buffer size to prevent infinite read
    # log every received buffer

    def read_frame_from_serial(self):
        frame_buffer = bytearray()

        while not self.event_stop.is_set():
            self.event_heartbeat.set()

            # Check for data availability
            if self.serial.in_waiting > 0:
                data = self.serial.read(self.serial.in_waiting)
                frame_buffer += data
                self.serial_timeout = False

                # Update the last read time
                self.last_read_time = time.time()

            # Check if the frame interval has elapsed
            if (time.time() - self.last_read_time) > 3:
                if len(frame_buffer) > 0:
                    self.serial_timeout = False

                    self.last_frame_time = time.time()  # Update last frame time
                    return frame_buffer
                else:
                    # Reset for the next frame
                    frame_buffer = bytearray()

            # Handle potential buffer overflow
            if len(frame_buffer) > self.max_buffer_size:
                self.logger.consoleLogger.warn("Receiver buffer overflow!")
                return frame_buffer

            # Check for serial timeout
            current_time = time.time()
            if (
                self.last_read_time
                and current_time - self.last_read_time > SERIAL_TIMEOUT
                and not self.serial_timeout
                and time.time() > (self.reboot_start_time + 30)
            ) or (
                current_time - self.last_frame_time > SERIAL_TIMEOUT
                and not self.serial_timeout
                and time.time() > (self.reboot_start_time + 30)
            ):
                self.handle_serial_timeout()
                return None

            if self.serial_timeout:
                return None

            time.sleep(0.001)  # Sleep for 1 ms to reduce CPU usage

        return None

    def handle_serial_timeout(self):
        self.serial_timeout = True

        self.logger.consoleLogger.warn("Serial Communication Timeout!")
        self.logger.dataLogger.info(
            {
                "type": "Serial " + self.name,
                "id": CLIENT_SERIAL_TIMEOUT,
                "timestamp": time.time(),
                "event": "Serial Timeout",
            }
        )
        self.power_down_DUT(self.lindy_port, self.lindy_switch)

    def power_down_DUT(self, select_power_switch, power_IP):
        return_code = 0
        # Call switch to power down
        return_code = ps._lindy_switch("OFF", select_power_switch, power_IP)

        self.device_is_off = True

        self.reboot_start_time = time.time()

        self.logger.consoleLogger.warn(
            f"Powering down {select_power_switch} at {power_IP}:: {return_code}"
        )

    def power_up_DUT(self, select_power_switch, power_IP):
        return_code = 0

        if (time.time() > self.reboot_start_time + 10) and self.device_is_off == True:
            # Call switch to power up
            return_code = ps._lindy_switch("ON", select_power_switch, power_IP)

            self.logger.consoleLogger.warn(
                f"Powering up {select_power_switch} at {power_IP}:: {return_code}"
            )
            self.device_is_off = False
            self.serial.flushInput()
            self.serial.flushOutput()

        if time.time() > (self.reboot_start_time + 30):
            self.logger.consoleLogger.info("Clearing timeout!")
            self.serial_timeout = False
