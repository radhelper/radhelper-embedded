import logging
import logging.handlers
import logging.config
import pty
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

    console_level = None
    data_logger_level = None
    coloredlogs_level = None
    name = None

    def __init__(
        self,
        mode="",
        log_folder: str = "logs",
        verbose=2,
        log_rotate_interval=10,
    ):

        self.name = mode
        self.setup_folder_file(log_folder)
        self.setup_level(verbose)

        self.file_handler(log_rotate_interval)
        if self.name == "Server":
            self.stream_handler()
        else:
            self.stream_handler_dedicated()

    def file_handler(self, log_rotate_interval):

        self.fileHandler = CustomTimedRotatingFileHandler(
            self.logfile, when="M", interval=log_rotate_interval, backupCount=0
        )  # No backupCount to avoid deleting old files
        self.fileHandler.setLevel(self.data_logger_level)  # Set based on verbose level

        # Formatter for file handler
        file_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)8s] [%(name)6s] %(message)s"
        )
        self.fileHandler.setFormatter(file_fmt)

        # Logger for file output
        self.dataLogger = logging.getLogger(self.name)
        self.dataLogger.addHandler(self.fileHandler)
        self.dataLogger.setLevel(self.data_logger_level)  # Set based on verbose level
        self.dataLogger.propagate = False

    def stream_handler_dedicated(self):
        # Dynamically create a new pseudo-terminal
        master_fd, slave_fd = pty.openpty()  # Create a new pseudo-terminal
        terminal_path = os.ttyname(slave_fd)  # Get the TTY path of the slave end

        link_path = "/tmp/logger_" + self.name

        # Check if the symbolic link already exists
        if os.path.islink(link_path) or os.path.exists(link_path):
            os.remove(link_path)  # Remove the existing symlink or file

        # Create a symbolic link from the TTY to a fixed path
        os.symlink(terminal_path, link_path)

        try:
            # Open the master side of the PTY for writing
            terminal_stream = os.fdopen(master_fd, "w", buffering=1)  # Line buffering
        except FileNotFoundError:
            raise Exception(f"Terminal {terminal_path} not found")

        # Set up logger if it doesn't exist
        if not hasattr(self, "consoleLogger"):
            self.consoleLogger = logging.getLogger(self.name)

        # Set up new stream handler
        self.streamHandler = StreamHandler(terminal_stream)
        self.streamHandler.setLevel(self.console_level)  # Set based on verbose level

        # Formatter for stream handler
        console_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)8s] [%(name)6s] %(message)s"
        )
        self.streamHandler.setFormatter(console_fmt)

        # Attach the new handler
        self.consoleLogger.addHandler(self.streamHandler)
        self.consoleLogger.setLevel(self.console_level)

        # Set up colored logs for better readability in the new terminal
        fmt = "%(asctime)s [%(levelname)8s] [%(name)6s] %(message)s"
        coloredlogs.install(
            logger=self.consoleLogger,
            level=self.coloredlogs_level,
            fmt=fmt,
            stream=terminal_stream,
        )

        # Make sure the stream gets flushed
        terminal_stream.flush()

    def stream_handler(
        self,
    ):
        self.streamHandler = StreamHandler(sys.stdout)
        self.streamHandler.setLevel(self.console_level)  # Set based on verbose level

        # Formatter for stream handler
        console_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)8s] [%(name)6s] %(message)s"
        )
        self.streamHandler.setFormatter(console_fmt)

        # Central logger for console output
        self.consoleLogger = logging.getLogger(self.name)
        self.consoleLogger.addHandler(self.streamHandler)
        self.consoleLogger.setLevel(
            self.console_level
        )  # Ensure consoleLogger's level is set

        # Set up colored logs for better readability in the console
        fmt = "%(asctime)s [%(levelname)8s] [%(name)6s] %(message)s"
        coloredlogs.install(
            logger=self.consoleLogger, level=self.coloredlogs_level, fmt=fmt
        )

    def setup_level(self, verbose):
        # Determine logging levels based on verbose parameter
        if verbose >= 3:
            self.console_level = logging.DEBUG
            self.coloredlogs_level = "DEBUG"
            self.data_logger_level = logging.DEBUG
        elif verbose == 2:
            self.console_level = logging.INFO
            self.coloredlogs_level = "INFO"
            self.data_logger_level = logging.DEBUG
        elif verbose == 1:
            self.console_level = logging.WARNING
            self.coloredlogs_level = "WARNING"
            self.data_logger_level = logging.DEBUG
        else:  # verbose == 0
            self.console_level = logging.ERROR
            self.coloredlogs_level = "ERROR"
            self.data_logger_level = (
                logging.DEBUG
            )  # Typically, file logging remains at DEBUG

    def setup_folder_file(self, log_folder):
        # Ensure subfolder for mode exists within the main log_folder
        mode_log_folder = os.path.join(log_folder, self.name)
        if not os.path.exists(mode_log_folder):
            os.makedirs(mode_log_folder)

        # Base filename with initial timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{self.name}_{timestamp}.log"
        self.logfile = os.path.join(mode_log_folder, filename)
