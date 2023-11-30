import logging
import logging.handlers
import os
import pickle
import socketserver
import struct
import sys
import time
from logging import FileHandler, StreamHandler
from logging.handlers import SocketHandler, TimedRotatingFileHandler
from typing import Literal

import coloredlogs
from pythonjsonlogger import jsonlogger


class LoggerStreamHandler(socketserver.StreamRequestHandler):
    """Handler for a streaming logging request.

    This basically logs the record using whatever logging policy is
    configured locally.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        self.server.logger.consoleLogger.info(f"Client '{self.client_address}' connected.")
        self.server.clients.append(self.client_address)
        while True:
            self.server.last_message = time.time()
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack('>L', chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unPickle(chunk)
            record = logging.makeLogRecord(obj)

            self.handleLogRecord(record)
        self.server.clients.remove(self.client_address)
        self.server.logger.consoleLogger.error(f"Client '{self.client_address}' disconnected.")

    def unPickle(self, data):
        return pickle.loads(data)

    def handleLogRecord(self, record):
        # if a name is specified, we use the named logger rather than the one
        # implied by the record.
        if self.server.logname is not None:
            name = self.server.logname
        else:
            name = record.name
        logger = logging.getLogger(name)
        # N.B. EVERY record gets logged. This is because Logger.handle
        # is normally called AFTER logger-level filtering. If you want
        # to do filtering, do it at the client end to save wasting
        # cycles and network bandwidth!
        record.name = self.client_address[0]
        logger.handle(record)


class Logger:

    def __init__(self,
                 mode: Literal['Client', 'Server'] = 'Client',
                 log_folder: str = 'logs',
                 ip_address: str = '127.0.0.1',
                 port: int = logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                 verbose = 0,
                 log_rotate_interval = 10):

        # Setup File logger
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)

        filename = mode + '_' + time.strftime("%Y%m%d-%H%M%S") + '.log' 

        self.logfile = os.path.join(log_folder, filename)
        print(f"Store logs to {self.logfile}.")
        if mode == 'Client':
            self.fileHandler: logging.Handler = TimedRotatingFileHandler(self.logfile,
                                                                         when = 'M',
                                                                         interval = log_rotate_interval)
        elif mode == 'Server':
            self.fileHandler: logging.Handler = FileHandler(self.logfile, mode = 'a')
        self.fileHandler.setLevel(logging.DEBUG)

        self.streamHandler: logging.Handler = StreamHandler(sys.stdout)
        if verbose == 0:
            self.streamHandler.setLevel(logging.ERROR)
        elif verbose == 1:
            self.streamHandler.setLevel(logging.WARN)
        elif verbose == 2:
            self.streamHandler.setLevel(logging.INFO)
        elif verbose >= 3:
            self.streamHandler.setLevel(logging.DEBUG)

        self.dataLogger: logging.Logger = logging.getLogger('Logger')
        self.dataLogger.addHandler(self.fileHandler)
        self.dataLogger.addHandler(self.streamHandler)
        self.dataLogger.setLevel(logging.DEBUG)

        self.dataLogger.propagate = False

        clientLogger: logging.Logger = logging.getLogger('Client')
        serverLogger: logging.Logger = logging.getLogger('Server')
        clientLogger.propagate = False
        serverLogger.propagate = False

        fmt = "%(asctime)s [%(levelname)8s] [%(name)12s] %(message)s"
        if verbose == 0:
            coloredlogs.install(logger = clientLogger, level = "INFO", fmt = fmt)
            coloredlogs.install(logger = serverLogger, level = "INFO", fmt = fmt)
        elif verbose >= 1:
            coloredlogs.install(logger = clientLogger, level = "DEBUG", fmt = fmt)
            coloredlogs.install(logger = serverLogger, level = "DEBUG", fmt = fmt)

        # Setup TCP sender or receiver
        if mode == 'Client':
            self.consoleLogger: logging.Logger = clientLogger

            self.socketHandler: logging.Handler = SocketHandler(ip_address, port)
            self.socketHandler.setLevel(logging.DEBUG)

            jsonFmt = jsonlogger.JsonFormatter("%(message)s",)
            self.fileHandler.setFormatter(jsonFmt)

            self.dataLogger.addHandler(self.socketHandler)
            self.consoleLogger.addHandler(self.socketHandler)

        if mode == 'Server':
            self.consoleLogger: logging.Logger = serverLogger

            stringFmt = logging.Formatter("%(name)s %(message)s",)
            self.fileHandler.setFormatter(stringFmt)
            self.streamHandler.setFormatter(stringFmt)

            self.socketReceiver = LoggerSocketReceiver(ip_address, port, LoggerStreamHandler)
            self.socketReceiver.daemon_threads = True
            self.socketReceiver.bind_logger(self)


class LoggerSocketReceiver(socketserver.ThreadingTCPServer):
    """
    Simple TCP socket-based logging receiver suitable for testing.
    """

    allow_reuse_address = True

    def __init__(self,
                 host = '0.0.0.0',
                 port = logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                 handler = LoggerStreamHandler):

        socketserver.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1
        self.logname = None
        self.last_message = time.time()
        self.clients = []

    def bind_logger(self, logger: Logger):
        self.logger = logger

    def start(self):
        import select
        abort = 0
        self.logger.consoleLogger.info('Start TCP log server.')
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()], [], [], self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort
