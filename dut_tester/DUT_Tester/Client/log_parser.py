#!/usr/bin/python3
import sys
import json
import glob
import os
from payload_decoding import parse_payload 

# Sorting function based on both keys and values
def sort_timestamp(d):
    return (d['timestamp'])

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


def parse_dut_tester_log(file_paths):
    dictionaries = []
    for file_path in file_paths:
        with open(file_path, 'r') as file:
            for json_line in file:
                json_line_parsed = json.loads(json_line)
                if 'data' in json_line_parsed:
                    frame = parse_data_as_object(json_line_parsed['data'])
                    if frame == 1:
                        continue
                    parsed_payload = (json_line_parsed['timestamp'],) + parse_payload(frame.payload, frame.frame_id)
                    keys = ['timestamp', 'total_errors', 'mcycle', 'minstret', 'imem_se', 'imem_de', 'dmem_se', 'dmem_de', 'regfile_se', 'regfile_de', 'iv', 'jump', 'branch', 'dsp_t', 'trap', 'illegal']
                    mapping = {num: key for num, key in zip(keys, parsed_payload)}
                    dictionaries.append(mapping)
                elif 'event' in json_line_parsed:
                    dictionaries.append(json_line_parsed)
                else:
                    continue
    for dict in sorted(dictionaries, key=sort_timestamp):
        print(dict)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: ./log_parser.py directory filepath")
        sys.exit(1)

    file_pattern = sys.argv[2]
    directory_path = sys.argv[1]  # You can specify the directory if needed

    # Use glob to find all files matching the pattern
    file_paths = glob.glob(os.path.join(directory_path, file_pattern))


    parse_dut_tester_log(file_paths)