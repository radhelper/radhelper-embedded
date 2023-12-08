class DataFrame:
    def __init__(self, header, frame_id, payload_length, payload, crc_bytes, tail):
        self.header = header,
        self.frame_id = frame_id,
        self.payload_length = payload_length,
        self.payload = payload,
        self.crc_bytes = crc_bytes,
        self.tail = tail

def parse_data_as_object(data_str):
    if len(data_str) % 2 != 0 or data_str[0:2] != 'aa':
        print(f"Data string {data_str} not a valid data string!")
    try:
        frame_bytes = bytes.fromhex(data_str)
    except:
        return 1
    frame = DataFrame
    frame.header = frame_bytes[0]
    frame.frame_id = frame_bytes[1]
    frame.payload_length = frame_bytes[2]
    frame.payload = frame_bytes[3 : 3 + frame.payload_length]
    frame.crc_bytes = frame_bytes[3 + frame.payload_length : 5 + frame.payload_length]
    frame.tail = frame_bytes[-1]
    return frame

def parse_dut_tester_log(frame):
    dictionaries = []
    for file_path in file_paths:
        with open(file_path, 'r') as file:
            for json_line in file:
                json_line_parsed = json.loads(json_line)
                if 'data' in json_line_parsed:
                    frame = parse_data_as_object(json_line_parsed['data'])