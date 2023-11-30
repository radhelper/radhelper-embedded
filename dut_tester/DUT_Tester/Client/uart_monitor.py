import binascii
import os
import time
from threading import Event, Thread

import pigpio

from DUT_Tester.log_id import CLIENT_SERIAL_TIMEOUT, CLIENT_SERIAL_RX
from DUT_Tester.util import Logger

SERIAL_TIMEOUT = 20


class UARTMonitor(Thread):
    def __init__(
        self,
        logger: Logger,
        event_heartbeat: Event,
        event_stop: Event,
        freq=100,
        tty="/dev/serial0",
        baudrate=115200,
    ):
        Thread.__init__(self)
        self.deamon = True
        self.event_heartbeat = event_heartbeat
        self.event_stop = event_stop
        self.baudrate = baudrate
        self.tty = tty

        self.freq = freq
        self.logger = logger

        self.last_serial = time.time()

        self.serial_timeout = False

        self.PI = pigpio.pi()

    def run(self):
        self.event_heartbeat.set()

        self.logger.consoleLogger.info(f"Started UART Monitor Thread. [{os.getpid()}]")

        self.last_serial = time.time()

        serial = self.PI.serial_open("/dev/serial0", self.baudrate)

        while not self.event_stop.is_set():
            # Set heartbeat signal
            self.event_heartbeat.set()

            data_avaiable = self.PI.serial_data_available(serial)
            if data_avaiable:
                _, d = self.PI.serial_read(serial)
                d = d.rstrip(b"\x00")
                if len(d) > 0:
                    self.serial_timeout = False
                    self.last_serial = time.time()
                    try:
                        string = d.decode("utf-8")
                    except:
                        string = str(binascii.hexlify(d), "ascii")
                    self.logger.dataLogger.info(
                        {
                            "type": "Serial",
                            "id": CLIENT_SERIAL_RX,
                            "timestamp": time.time(),
                            "data": string,
                        }
                    )
                    self.logger.consoleLogger.info("[Serial] " + string.rstrip("\n"))

            if (
                time.time() - self.last_serial > SERIAL_TIMEOUT
                and not self.serial_timeout
            ):
                self.serial_timeout = True
                self.logger.consoleLogger.warn("Serial Communication Timeout!")
                self.logger.dataLogger.info(
                    {
                        "type": "Serial",
                        "id": CLIENT_SERIAL_TIMEOUT,
                        "timestamp": time.time(),
                        "event": "Serial Timeout",
                    }
                )

            time.sleep(1 / self.freq)

        self.PI.serial_close(serial)
        self.logger.consoleLogger.info(f"Stopped Data Monitor Thread. [{os.getpid()}]")
