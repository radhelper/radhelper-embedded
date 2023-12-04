import struct

# +--------+--------------------+-------------+---------------+
# | Format | C Type             | Python type | Standard size |
# +--------+--------------------+-------------+---------------+
# | x      | pad byte           | no value    | (7)           |
# | c      | char               | bytes       | 1             |
# | b      | signed char        | integer     | 1             |
# | B      | unsigned char      | integer     | 1             |
# | ?      | _Bool              | bool        | 1             |
# | h      | short              | integer     | 2             |
# | H      | unsigned short     | integer     | 2             |
# | i      | int                | integer     | 4             |
# | I      | unsigned int       | integer     | 4             |
# | l      | long               | integer     | 4             |
# | L      | unsigned long      | integer     | 4             |
# | q      | long long          | integer     | 8             |
# | Q      | unsigned long long | integer     | 8             |
# | n      | ssize_t            | integer     | (3)           |
# | N      | size_t             | integer     | (3)           |
# | e      | (6)                | float       | 2             |
# | f      | float              | float       | 4             |
# | d      | double             | float       | 8             |
# | s      | char[]             | bytes       | (9)           |
# | p      | char[]             | bytes       | (8)           |
# | P      | void*              | integer     | (5)           |
# +--------+--------------------+-------------+---------------+


frame_id_formatting = {
    "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB": 0,  # test frame
    # "II": 1,  # fini
    "IIIIIIIIIIIIII": 1,  # fini
    "IIIIII": 16,  # exception
}


def parse_payload(data, frame_id):
    # Ensure that the data is a bytes object
    # if not isinstance(data, bytes):
    #     raise ValueError("Data must be bytes")

    # Find the format string for the given frame_id
    format_str = None
    for fmt_str, id in frame_id_formatting.items():
        if id == frame_id:
            format_str = fmt_str
            break

    if format_str is None:
        raise ValueError(f"No format string found for frame ID {frame_id}")

    # Unpack the data dynamically based on the format string
    try:
        unpacked_data = struct.unpack(format_str, data)
    except struct.error as e:
        raise ValueError(
            f"Error unpacking data with format {format_str}: {e}, data {data}"
        )

    # # Convert bytes to string for field4 if necessary
    # field4 = field4.decode("utf-8").rstrip("\x00")

    # for field in unpacked_data:
    #     print(hex(field))

    return unpacked_data
