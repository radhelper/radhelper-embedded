import logging
import logging.handlers
import logging.config
import os
import sys
import time
import coloredlogs
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime


class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(
        self,
        filename,
        when="M",
        interval=1,
        backupCount=0,
        encoding=None,
        delay=False,
        utc=False,
    ):
        self.originalDir, self.originalBasename = os.path.split(filename)
        super().__init__(filename, when, interval, backupCount, encoding, delay, utc)

    def doRollover(self):
        """
        Overriding the doRollover method to create a new file with the same name pattern.
        """
        currentTime = int(time.time())
        self.stream.close()
        # Calculate the new rollover time
        newRolloverAt = self.computeRollover(currentTime)

        # Generate new timestamp for the new filename
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        new_filename = f"{self.originalBasename.split('_')[0]}_{timestamp}.log"
        print(new_filename)
        self.baseFilename = os.path.join(self.originalDir, new_filename)

        # Open a new file with the new base filename
        self.stream = self._open()

        # Update the rollover time
        self.rolloverAt = newRolloverAt


class Logger:
    """
    A custom logging class to handle logging for both console and file outputs with log rotation.

    Attributes:
        name (str): The name specifier for the logger, used to distinguish between different loggers.
        logfile (str): The path to the log file where log messages will be stored.
        fileHandler (logging.Handler): The handler for writing log messages to a file with rotation.
        streamHandler (logging.Handler): The handler for writing log messages to the console.
        dataLogger (logging.Logger): The logger instance for file output.
        consoleLogger (logging.Logger): The logger instance for console output.

    Args:
        mode (Literal['DUT', 'Server']): Specifies the mode of the logger, used in log file naming.
        log_folder (str): The folder where log files will be stored. Default is 'logs'.
        verbose (int): Verbosity level for logging:
            0 - ERROR level for console, DEBUG level for file
            1 - WARNING level for console, DEBUG level for file
            2 - INFO level for console, DEBUG level for file
            3 - DEBUG level for both console and file
        log_rotate_interval (int): The interval (in minutes) at which the log files will be rotated.

    Example:
        logger = Logger(mode='Server', verbose=2)
        logger.info("This is an info message")
    """

    def __init__(
        self, mode="", log_folder: str = "logs", verbose=2, log_rotate_interval=10
    ):

        # Determine logging levels based on verbose parameter
        if verbose >= 3:
            console_level = logging.DEBUG
            coloredlogs_level = "DEBUG"
            data_logger_level = logging.DEBUG
        elif verbose == 2:
            console_level = logging.INFO
            coloredlogs_level = "INFO"
            data_logger_level = logging.DEBUG
        elif verbose == 1:
            console_level = logging.WARNING
            coloredlogs_level = "WARNING"
            data_logger_level = logging.DEBUG
        else:  # verbose == 0
            console_level = logging.ERROR
            coloredlogs_level = "ERROR"
            data_logger_level = (
                logging.DEBUG
            )  # Typically, file logging remains at DEBUG

        self.name = mode

        # Ensure subfolder for mode exists within the main log_folder
        mode_log_folder = os.path.join(log_folder, mode)
        if not os.path.exists(mode_log_folder):
            os.makedirs(mode_log_folder)

        # Base filename with initial timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{mode}_{timestamp}.log"
        self.logfile = os.path.join(mode_log_folder, filename)
        print(f"Store logs to {self.logfile}.")

        self.fileHandler = CustomTimedRotatingFileHandler(
            self.logfile, when="M", interval=log_rotate_interval, backupCount=0
        )  # No backupCount to avoid deleting old files
        self.fileHandler.setLevel(data_logger_level)  # Set based on verbose level

        self.streamHandler = StreamHandler(sys.stdout)
        self.streamHandler.setLevel(console_level)  # Set based on verbose level

        # Formatter for file handler
        file_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)8s] [%(name)6s] %(message)s"
        )
        self.fileHandler.setFormatter(file_fmt)

        # Formatter for stream handler
        console_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)8s] [%(name)6s] %(message)s"
        )
        self.streamHandler.setFormatter(console_fmt)

        # Logger for file output
        self.dataLogger = logging.getLogger(self.name)
        self.dataLogger.addHandler(self.fileHandler)
        self.dataLogger.setLevel(data_logger_level)  # Set based on verbose level
        self.dataLogger.propagate = False

        # Central logger for console output
        self.consoleLogger = logging.getLogger(self.name)
        self.consoleLogger.addHandler(self.streamHandler)
        self.consoleLogger.setLevel(
            console_level
        )  # Ensure consoleLogger's level is set

        # Set up colored logs for better readability in the console
        fmt = "%(asctime)s [%(levelname)8s] [%(name)6s] %(message)s"
        coloredlogs.install(logger=self.consoleLogger, level=coloredlogs_level, fmt=fmt)
