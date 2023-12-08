#!/usr/bin/python3
import sys
import json
import glob
import os
import subprocess
import paramiko
import time
from datetime import datetime, timezone
from payload_decoding import parse_payload 

crcTable = [
    0x0000,
    0x1021,
    0x2042,
    0x3063,
    0x4084,
    0x50A5,
    0x60C6,
    0x70E7,
    0x8108,
    0x9129,
    0xA14A,
    0xB16B,
    0xC18C,
    0xD1AD,
    0xE1CE,
    0xF1EF,
    0x1231,
    0x0210,
    0x3273,
    0x2252,
    0x52B5,
    0x4294,
    0x72F7,
    0x62D6,
    0x9339,
    0x8318,
    0xB37B,
    0xA35A,
    0xD3BD,
    0xC39C,
    0xF3FF,
    0xE3DE,
    0x2462,
    0x3443,
    0x0420,
    0x1401,
    0x64E6,
    0x74C7,
    0x44A4,
    0x5485,
    0xA56A,
    0xB54B,
    0x8528,
    0x9509,
    0xE5EE,
    0xF5CF,
    0xC5AC,
    0xD58D,
    0x3653,
    0x2672,
    0x1611,
    0x0630,
    0x76D7,
    0x66F6,
    0x5695,
    0x46B4,
    0xB75B,
    0xA77A,
    0x9719,
    0x8738,
    0xF7DF,
    0xE7FE,
    0xD79D,
    0xC7BC,
    0x48C4,
    0x58E5,
    0x6886,
    0x78A7,
    0x0840,
    0x1861,
    0x2802,
    0x3823,
    0xC9CC,
    0xD9ED,
    0xE98E,
    0xF9AF,
    0x8948,
    0x9969,
    0xA90A,
    0xB92B,
    0x5AF5,
    0x4AD4,
    0x7AB7,
    0x6A96,
    0x1A71,
    0x0A50,
    0x3A33,
    0x2A12,
    0xDBFD,
    0xCBDC,
    0xFBBF,
    0xEB9E,
    0x9B79,
    0x8B58,
    0xBB3B,
    0xAB1A,
    0x6CA6,
    0x7C87,
    0x4CE4,
    0x5CC5,
    0x2C22,
    0x3C03,
    0x0C60,
    0x1C41,
    0xEDAE,
    0xFD8F,
    0xCDEC,
    0xDDCD,
    0xAD2A,
    0xBD0B,
    0x8D68,
    0x9D49,
    0x7E97,
    0x6EB6,
    0x5ED5,
    0x4EF4,
    0x3E13,
    0x2E32,
    0x1E51,
    0x0E70,
    0xFF9F,
    0xEFBE,
    0xDFDD,
    0xCFFC,
    0xBF1B,
    0xAF3A,
    0x9F59,
    0x8F78,
    0x9188,
    0x81A9,
    0xB1CA,
    0xA1EB,
    0xD10C,
    0xC12D,
    0xF14E,
    0xE16F,
    0x1080,
    0x00A1,
    0x30C2,
    0x20E3,
    0x5004,
    0x4025,
    0x7046,
    0x6067,
    0x83B9,
    0x9398,
    0xA3FB,
    0xB3DA,
    0xC33D,
    0xD31C,
    0xE37F,
    0xF35E,
    0x02B1,
    0x1290,
    0x22F3,
    0x32D2,
    0x4235,
    0x5214,
    0x6277,
    0x7256,
    0xB5EA,
    0xA5CB,
    0x95A8,
    0x8589,
    0xF56E,
    0xE54F,
    0xD52C,
    0xC50D,
    0x34E2,
    0x24C3,
    0x14A0,
    0x0481,
    0x7466,
    0x6447,
    0x5424,
    0x4405,
    0xA7DB,
    0xB7FA,
    0x8799,
    0x97B8,
    0xE75F,
    0xF77E,
    0xC71D,
    0xD73C,
    0x26D3,
    0x36F2,
    0x0691,
    0x16B0,
    0x6657,
    0x7676,
    0x4615,
    0x5634,
    0xD94C,
    0xC96D,
    0xF90E,
    0xE92F,
    0x99C8,
    0x89E9,
    0xB98A,
    0xA9AB,
    0x5844,
    0x4865,
    0x7806,
    0x6827,
    0x18C0,
    0x08E1,
    0x3882,
    0x28A3,
    0xCB7D,
    0xDB5C,
    0xEB3F,
    0xFB1E,
    0x8BF9,
    0x9BD8,
    0xABBB,
    0xBB9A,
    0x4A75,
    0x5A54,
    0x6A37,
    0x7A16,
    0x0AF1,
    0x1AD0,
    0x2AB3,
    0x3A92,
    0xFD2E,
    0xED0F,
    0xDD6C,
    0xCD4D,
    0xBDAA,
    0xAD8B,
    0x9DE8,
    0x8DC9,
    0x7C26,
    0x6C07,
    0x5C64,
    0x4C45,
    0x3CA2,
    0x2C83,
    0x1CE0,
    0x0CC1,
    0xEF1F,
    0xFF3E,
    0xCF5D,
    0xDF7C,
    0xAF9B,
    0xBFBA,
    0x8FD9,
    0x9FF8,
    0x6E17,
    0x7E36,
    0x4E55,
    0x5E74,
    0x2E93,
    0x3EB2,
    0x0ED1,
    0x1EF0,
]

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

def decode_frame(frame_bytes):
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

    if crc_check is False:
        print(f"CRC Check failed!")
    else:
        data = parse_payload(payload, frame_id)

    return data

def check_crc(payload, payload_length, crc_value):
        INITIAL_REMAINDER = 0xFFFF
        FINAL_XOR_VALUE = 0x0000
        remainder = INITIAL_REMAINDER

        for byte in range(payload_length):
            data = payload[byte] ^ (remainder >> (16 - 8))
            remainder = crcTable[data] ^ (remainder << 8) & 0xFFFF

        return crc_value == (remainder ^ FINAL_XOR_VALUE)

def parse_dut_tester_log(file_paths, data_filter):
    frames = []
    frame_parsing_errors = 0
    crc_errors = 0
    filtered_frames = []
    for file_path in file_paths:
        with open(file_path, 'r') as file:
            for json_line in file:
                # Parse frame
                frame = json.loads(json_line)
                frames.append(frame)

    # Sort frames based on timestamp
    sorted_frames = sorted(frames, key=lambda x: x["timestamp"])

    previous_entry = None
    for frame in sorted_frames:
        frame['timestamp'] = str(datetime.utcfromtimestamp(float(frame['timestamp'])).replace(tzinfo=timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f UTC'))
        if 'data' in frame:
            try:
                decoded_frame = decode_frame(bytes.fromhex(frame['data']))
                frame['data'] = decoded_frame
                if decoded_frame == None:
                    crc_errors += 1
            except Exception as error:
                frame_parsing_errors += 1
                print(f"Parsing error! {error}")

    previous_entry = None
    # Filtering duplicate payloads out
    for frame in sorted_frames:
        if (previous_entry is None or frame['data'] != previous_entry):
            #frame['payload'] = frame.pop('data')
            filtered_frames.append(frame)

    for frame in filtered_frames:
        if data_filter.isnumeric():
            if frame['id'] == int(data_filter):
                print(frame)
        else:
            print(frame)

    print(f"CRC errors: {crc_errors}")
    print(f"Frame parsing errors: {frame_parsing_errors}")

    # Filter on frame id
    # Remove duplicate payload entries (only transitions)

    # print(frames)

    #             print(json_line)
    #             json_line_parsed = json.loads(json_line)
    #             if 'data' in json_line_parsed:
    #                 frame = parse_data_as_object(json_line_parsed['data'])
    #                 if frame == 1:
    #                     continue
    #                 parsed_payload = (json_line_parsed['timestamp'],) + parse_payload(frame.payload, frame.frame_id)
    #                 keys = ['timestamp', 'total_errors', 'mcycle', 'minstret', 'imem_se', 'imem_de', 'dmem_se', 'dmem_de', 'regfile_se', 'regfile_de', 'iv', 'jump', 'branch', 'dsp_t', 'trap', 'illegal']
    #                 mapping = {num: key for num, key in zip(keys, parsed_payload)}
    #                 dictionaries.append(mapping)
    #             elif 'event' in json_line_parsed:
    #                 keys = ['type', 'id', 'timestamp', 'event']
    #                 # print(json_line_parsed)
    #                 dictionaries.append(json_line_parsed)
    #             elif 'CRC check' in json_line_parsed:
    #                 dictionaries.append(json_line_parsed)
    #             else:
    #                 continue
    # previous_entry = None
    # for dict in sorted(dictionaries, key=sort_timestamp):
    #     utc_timestamp = str(datetime.utcfromtimestamp(float(dict['timestamp'])).replace(tzinfo=timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f UTC'))
    #     dict['timestamp'] = utc_timestamp
        # if (data_filter == "*"):
            # print(dict)
        # elif (data_filter in dict) and (previous_entry is None or dict[data_filter] != previous_entry):
            # print(dict)
            # previous_entry = dict[data_filter]

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: ./log_parser.py directory pattern filter")
        sys.exit(1)

    directory_path = sys.argv[1]  # You can specify the directory if needed
    file_pattern = sys.argv[2]
    data_filter = sys.argv[3]
    
    while True:
        # Use glob to find all files matching the pattern
        file_paths = glob.glob(os.path.join(directory_path, file_pattern))

        parse_dut_tester_log(file_paths, data_filter)

        time.sleep(5)