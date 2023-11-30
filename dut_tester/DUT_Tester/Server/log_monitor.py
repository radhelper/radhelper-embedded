from threading import Event, Thread

from DUT_Tester.log_id import *
from DUT_Tester.util import Logger


class LogMonitor(Thread):
    def __init__(
        self,
        logger: Logger,
        event_stop: Event,
    ):
        Thread.__init__(self)
        self.deamon = True
        self.logger = logger

        self.event_stop = event_stop

    def run(self):
        self.logger.socketReceiver.start()
