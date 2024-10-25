# Python Project: Frame Decoder and CRC Table

## Overview
This project contains two main components: a frame decoder and a CRC table. The frame decoder is responsible for parsing and decoding packet frames based on predefined formats. The CRC table provides a lookup table for CRC calculations.

## Files
- `crc_table.py`: Contains the CRC lookup table.
- `frame_decoder.py`: Contains the implementation of the `PacketFrame` class for decoding packet frames.

## Usage
1. Ensure that the `frame_id_formatting.yaml` configuration file is present in the same directory as the scripts.
2. Example usage of the `PacketFrame` class:

    ```python
    from frame_decoder import PacketFrame

    # Example packet data
    header = b'\x01'
    frame_id = b'\x02'
    payload_length = 5
    payload = b'\x11\x22\x33\x44\x55'
    crc_bytes = b'\x12\x34'
    tail = b'\xFF'

    packet = PacketFrame(header, frame_id, payload_length, payload, crc_bytes, tail)

    # Get default formatted string
    print(packet.format_default())

    # Get hex formatted string
    print(packet.format_hex())

    # Get log message in default format
    print(packet.get_log_message())

    # Get log message in hex format
    print(packet.get_log_message(format_type="hex"))

    # Get decoded payload
    try:
        decoded_payload = packet.parse_payload()
        print(decoded_payload)
    except ValueError as e:
        print(e)
    ```

## Configuration
The `frame_id_formatting.yaml` file should contain the formatting strings for different frame IDs. Example configuration:

```yaml
frame_id_formatting:
  ">B": 1
  ">H": 2
  ">I": 3
```

## CRC Table
The crc_table.py file contains a precomputed CRC table for fast CRC calculations. Example of using the CRC table:

```python
from crc_table import crcTable

def calculate_crc(data):
    crc = 0xFFFF
    for byte in data:
        crc = (crc << 8) ^ crcTable[((crc >> 8) ^ byte) & 0xFF]
    return crc & 0xFFFF

# Example data
data = b'\x01\x02\x03\x04'
crc_value = calculate_crc(data)
print(f"CRC: {crc_value:04X}")
```