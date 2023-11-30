from enum import Enum, auto


class ErrorCodes(Enum):
    """Error codes used to identify status in this test"""

    SUCCESS = auto()
    # When all tries of telnet failed
    TELNET_CONNECTION_ERROR = auto()
    # Codes for RebootMachine
    GENERAL_ERROR = auto()
    HTTP_ERROR = auto()
    CONNECTION_ERROR = auto()
    TIMEOUT_ERROR = auto()
    MAXIMUM_APP_REBOOT_REACHED = auto()
    MAXIMUM_OS_REBOOT_REACHED = auto()
    DISABLED_SOFT_OS_REBOOT = auto()
    HOST_UNREACHABLE = auto()

    def __str__(self) -> str:
        """Override the str method
        :return: the name of the enum as string
        """
        return self.name