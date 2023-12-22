import struct
import log_codes as log
from crc_table import crcTable

"""
+--------+--------------------+-------------+---------------+
| Format | C Type             | Python type | Standard size |
+--------+--------------------+-------------+---------------+
| x      | pad byte           | no value    | (7)           |
| c      | char               | bytes       | 1             |
| b      | signed char        | integer     | 1             |
| B      | unsigned char      | integer     | 1             |
| ?      | _Bool              | bool        | 1             |
| h      | short              | integer     | 2             |
| H      | unsigned short     | integer     | 2             |
| i      | int                | integer     | 4             |
| I      | unsigned int       | integer     | 4             |
| l      | long               | integer     | 4             |
| L      | unsigned long      | integer     | 4             |
| q      | long long          | integer     | 8             |
| Q      | unsigned long long | integer     | 8             |
| n      | ssize_t            | integer     | (3)           |
| N      | size_t             | integer     | (3)           |
| e      | (6)                | float       | 2             |
| f      | float              | float       | 4             |
| d      | double             | float       | 8             |
| s      | char[]             | bytes       | (9)           |
| p      | char[]             | bytes       | (8)           |
| P      | void*              | integer     | (5)           |
+--------+--------------------+-------------+---------------+
"""


def parse_payload(data, frame_id, frame_id_formatting):
    """
    Parse the payload data based on the given frame ID and format string.

    Args:
        data (bytes): The payload data to be parsed.
        frame_id (int): The ID of the frame.
        frame_id_formatting (dict): A dictionary mapping frame IDs to format strings.

    Returns:
        tuple: The unpacked data as a tuple.

    Raises:
        ValueError: If the data is not a bytes object or if no format string is found for the given frame ID.
    """
    # Ensure that the data is a bytes object
    if not isinstance(data, bytes):
        raise ValueError("Data must be bytes")

    # Find the format string for the given frame_id
    format_str = None
    unpacked_data = ()
    for fmt_str, id in frame_id_formatting.items():
        if id == frame_id:
            format_str = fmt_str
            break

    error_code = 0

    if format_str is None:
        error_code = log.ERROR_NO_FORMAT
        raise ValueError(f"No format string found for frame ID {frame_id}")

    # Unpack the data dynamically based on the format string
    try:
        unpacked_data = struct.unpack(format_str, data)
    except struct.error as e:
        # print(f"Error unpacking data with format {format_str}: {e}, data {data}")
        error_code = log.ERROR_UNPACK

    return error_code, unpacked_data


def check_crc(payload, payload_length, crc_value):
    """
    Check the CRC (Cyclic Redundancy Check) value of the payload.

    Args:
        payload (bytes): The payload data.
        payload_length (int): The length of the payload.
        crc_value (int): The expected CRC value.

    Returns:
        bool: True if the CRC value matches the calculated CRC, False otherwise.
    """
    INITIAL_REMAINDER = 0xFFFF
    FINAL_XOR_VALUE = 0x0000
    remainder = INITIAL_REMAINDER

    for byte in range(payload_length):
        data = payload[byte] ^ (remainder >> (16 - 8))
        remainder = crcTable[data] ^ (remainder << 8) & 0xFFFF

    return crc_value == (remainder ^ FINAL_XOR_VALUE)


def decode_frame(frame_bytes, frame_id_formatting):
    # Desconstructing the frame
    header = frame_bytes[0]
    frame_id = frame_bytes[1]
    payload_length = frame_bytes[2]
    payload = frame_bytes[3 : 3 + payload_length]
    crc_bytes = frame_bytes[3 + payload_length : 5 + payload_length]
    tail = frame_bytes[-1]

    # Concatenating the CRC bytes into a single number
    # Assuming CRC is in big-endian format
    crc = (crc_bytes[0] << 8) | crc_bytes[1]

    # Converting payload to hex representation
    payload_hex = [hex(byte) for byte in payload]

    crc_check = check_crc(payload, payload_length, crc)

    data = None

    error_code = 0
    if crc_check is False:
        # print(f"CRC Check failed!")
        error_code = log.ERROR_CRC
    else:
        error_code, data = parse_payload(payload, frame_id, frame_id_formatting)

    return error_code, data, frame_id
