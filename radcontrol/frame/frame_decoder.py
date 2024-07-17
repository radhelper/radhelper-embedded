import struct
import yaml

# Load the frame_id_formatting from YAML file
with open("frame_id_formatting.yaml", "r") as file:
    config = yaml.safe_load(file)
    frame_id_formatting = config["frame_id_formatting"]


class PacketFrame:
    def __init__(self, header, frame_id, payload_length, payload, crc_bytes, tail):
        self.header = header  # 1 byte
        self.frame_id = frame_id  # 1 byte
        self.payload_length = payload_length  # 1 byte
        self.payload = payload  # N bytes
        self.crc_bytes = crc_bytes  # 2 bytes
        self.tail = tail  # 1 byte

    def to_hex(self, byte_array):
        return "".join(f"{byte:02x}" for byte in byte_array)

    def format_default(self):
        return (
            f"PacketFrame(header={self.header}, frame_id={self.frame_id}, "
            f"payload_length={self.payload_length}, payload={self.payload}, "
            f"crc_bytes={self.crc_bytes}, tail={self.tail})"
        )

    def format_hex(self):
        header_str = self.to_hex(self.header)
        frame_id_str = self.to_hex(self.frame_id)
        payload_length_str = f"0x{self.payload_length:02x}"
        payload_str = self.to_hex(self.payload)
        crc_bytes_str = self.to_hex(self.crc_bytes)
        tail_str = self.to_hex(self.tail)

        return f"{header_str},{frame_id_str},{payload_length_str},{payload_str},{crc_bytes_str},{tail_str}"

    def parse_payload(self):
        frame_id_int = int.from_bytes(self.frame_id, byteorder="big")
        format_str = None
        unpacked_data = ()

        for fmt_str, id in frame_id_formatting.items():
            if id == frame_id_int:
                format_str = fmt_str
                break

        if format_str is None:
            raise ValueError(f"No format string found for frame ID {frame_id_int}")

        try:
            unpacked_data = struct.unpack(format_str, self.payload)
        except struct.error as e:
            print(
                f"Error unpacking data with format {format_str}: {e}, data {self.payload}"
            )

        return unpacked_data

    def get_log_message(self, format_type="default"):
        if format_type == "hex":
            return self.format_hex()
        elif format_type == "decoded":
            return self.parse_payload()
        else:
            return self.format_default()

    def __str__(self):
        return self.format_default()
