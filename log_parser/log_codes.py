import pandas as pd
from payload_parser import decode_frame

ERROR_COMMUNICATION = 1
ERROR_CRC = 2
ERROR_UNPACK = 3
ERROR_UNEXPECTED = 4
ERROR_TIMEOUT = 5
ERROR_NO_DATA = 6
ERROR_NO_FORMAT = 7

FRAME_ID_TEST = 0
FRAME_ID_FINI = 1
FRAME_ID_EXCEPTION = 16


frame_id_formatting = {
    "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB": FRAME_ID_TEST,  # test frame
    "IIIIIIIIIIIIIII": FRAME_ID_FINI,  # fini
    "IIIIII": FRAME_ID_EXCEPTION,  # exception
}

keys = [
    "event",
    "timestamp",
    "total_errors",
    "mcycle",
    "minstret",
    "imem_se",
    "imem_de",
    "dmem_se",
    "dmem_de",
    "regfile_se",
    "regfile_de",
    "iv",
    "jump",
    "branch",
    "dsp_t",
    "trap",
    "illegal",
]
# keys = [
#     "event",
#     "timestamp",
#     "total_errors",
#     "mcycle",
#     "minstret",
#     "ir_c",
#     "wait_ii",
#     "wait_if",
#     "wait_mc",
#     "load",
#     "store",
#     "wait_ls",
#     "branch",
#     "tbranch",
#     "imem_ecc",
#     "dmem_ecc",
#     "regfile",
#     "iv",
# ]


def event_row(row, error_code=0, data_tup=None, frame_id=0):
    """
    Maps the values of a row to a dictionary with keys as specified in the 'keys' list.

    Args:
        row (dict): A dictionary representing a row of data.
        error_code (int, optional): The error code associated with the row. Defaults to 0.
        data_tup (tuple, optional): A tuple containing the parsed data values. Defaults to None.

    Returns:
        dict: A dictionary mapping the values of the row to the keys.
    """
    if error_code != 0:
        mapping = {num: 0 for num in keys}
        mapping["timestamp"] = row["timestamp"]
        mapping["event"] = error_code
    else:
        parsed_payload = (
            (row["event"],) + (row["timestamp"],) + tuple(map(int, data_tup))
        )
        if frame_id == FRAME_ID_FINI:
            mapping = {num: key for num, key in zip(keys, parsed_payload)}
        else:
            print(f"Detected an exception frame: {row}")

    return mapping


def parse_data(df):
    """
    Parses the data in a DataFrame and returns a new DataFrame with the parsed values.

    Args:
        df (pd.DataFrame): The DataFrame containing the data to be parsed.

    Returns:
        pd.DataFrame: A new DataFrame with the parsed values.
    """
    data_frame = []
    for index, row in df.iterrows():
        mapping = None
        if "id" in row and row["id"] == 20:
            if "data" in row and isinstance(row["data"], str) and row["data"] != "":
                try:
                    error_code, data_tup, frame_id = decode_frame(
                        bytes.fromhex(row["data"]), frame_id_formatting
                    )
                    mapping = event_row(row, error_code, data_tup, frame_id)
                except Exception as error:
                    mapping = event_row(row, error_code=ERROR_COMMUNICATION)
            else:
                mapping = event_row(row, error_code=ERROR_NO_DATA)
        else:
            mapping = event_row(row, error_code=ERROR_TIMEOUT)

        data_frame.append(mapping)

    data_frame = pd.DataFrame(data_frame)

    # Convert data columns to formated numeric values
    for column in data_frame.columns:
        if (
            column != "timestamp" or column != "event"
        ):  # Ignore the 'timestamp' and 'event' columns
            # Convert columns to numeric, coercing errors to NaN
            data_frame[column] = pd.to_numeric(data_frame[column], errors="coerce")

            # Option 1: Fill NaN values with 0 and convert to int
            data_frame[column] = data_frame[column].fillna(0).astype(int)

    return data_frame
