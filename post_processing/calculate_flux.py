#!/usr/bin/env python3
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# Time for each run
SECONDS_1h = 600


def read_count_file(in_file_name: str):
    """
    Read neutron log file
    :param in_file_name: neutron log filename
    :return: numpy array with all neutron lines
    """
    file_lines = list()
    with open(in_file_name, "r") as in_file:
        for line in in_file:
            # Sanity check, we require a date at the beginning of the line
            line_split = line.rstrip().split()
            if len(line_split) < 7:
                print(f"Ignoring line (malformed):{line}")
                continue
            year_date, day_time, sec_frac = line_split[0], line_split[1], line_split[2]
            fission_counter = float(line_split[6])

            # Generate datetime for line
            cur_dt = datetime.strptime(
                year_date + " " + day_time + sec_frac, "%d/%m/%Y %H:%M:%S.%f"
            )
            # It is faster to modify the lines on source
            file_lines.append(np.array([cur_dt, fission_counter]))
    return np.array(file_lines)


def get_fluency_flux(
    start_dt: datetime,
    end_dt,
    neutron_count: np.array,
    facility_factor: float,
    distance_attenuation: float,
):
    """
    -- Fission counters are the ChipIR counters -- index 6 in the ChipIR log
    -- Current Integral are the synchrotron output -- index 7 in the ChipIR log
    """
    three_seconds = pd.Timedelta(seconds=3)
    # Slicing the neutron count to use only the useful information
    # It is efficient because it returns a view of neutron count
    neutron_count_cut = neutron_count[
        (neutron_count[:, 0] >= start_dt)
        & (neutron_count[:, 0] <= (end_dt + three_seconds))
    ]
    beam_off_time, last_fission_counter = 0, None
    # Get the first from the list
    last_dt, first_fission_counter = neutron_count_cut[0]
    # Loop thought the neutron to find the beam off
    for cur_dt, fission_counter in neutron_count_cut[1:]:
        if fission_counter == last_fission_counter:
            beam_off_time += (cur_dt - last_dt).total_seconds()
        last_fission_counter = fission_counter
        last_dt = cur_dt

    interval_total_seconds = float((end_dt - start_dt).total_seconds())
    flux = (
        (last_fission_counter - first_fission_counter) * facility_factor
    ) / interval_total_seconds
    error_str = f"FLUX<0 {start_dt} {end_dt} {flux} {last_fission_counter} {interval_total_seconds} {beam_off_time}"
    assert flux >= 0, error_str

    flux *= distance_attenuation
    return flux, beam_off_time


def main():
    if len(sys.argv) < 3:
        print(
            f"Usage: {sys.argv[0]} <neutron counts input file> <distance facility_factor file>"
        )
        exit(1)

    neutron_count_file = sys.argv[1]
    distance_factor_file = sys.argv[2]

    # Load all distances before continue
    distance_data = pd.read_csv(distance_factor_file)
    # Replace the hours and the minutes to the last
    distance_data["start"] = distance_data["start"].apply(
        lambda row: datetime.strptime(row, "%d/%m/%Y %H:%M:%S")
    )
    distance_data["end"] = distance_data["end"].apply(
        lambda row: datetime.strptime(row, "%d/%m/%Y %H:%M:%S")
    )
    # -----------------------------------------------------------------------------------------------------------------
    # We need to read the neutron count files before calling get_fluency_flux
    neutron_count = read_count_file(neutron_count_file)
    # ----------------------------------------------------------------------------------------------------------------

    test_duration_hours = 1

    # # ECC-only
    # start_day = 17
    # start_hour = 00
    # start_min = 16
    # start_sec = 44
    # end_day = 17
    # end_hour = 5
    # end_min = 30
    # end_sec = 20

    # Simple
    # start_day = 16
    # start_hour = 13
    # start_min = 48
    # start_sec = 29
    # end_day = 16
    # end_hour = 19
    # end_min = 40
    # end_sec = 24

    # TMR
    # start_day = 16
    # start_hour = 21
    # start_min = 30
    # start_sec = 32
    # end_day = 17
    # end_hour = 0
    # end_min = 0
    # end_sec = 54

    # test
    start_day = 16
    start_hour = 15
    start_min = 30
    start_sec = 32
    end_day = 16
    end_hour = start_hour + 1
    end_min = start_min
    end_sec = start_sec

    # total_time = 3600 * (end_hour - start_hour) + (end_min -)

    for i in range(test_duration_hours):
        # for i in range(20):
        # start_hour = hours[i]
        # start_min = minutes[i]
        # start_sec = seconds[i]

        # end_hour = start_hour
        # end_min = start_min + 5

        # if end_min > 59:
        #     end_hour = start_hour + 1
        #     end_min = end_min - 60

        # print(
        #     f"{start_hour}:{start_min} -- {end_hour}:{end_min}",
        # )

        start_dt = datetime(2023, 5, start_day, start_hour, start_min, start_sec)
        end_dt = datetime(2023, 5, end_day, end_hour, end_min, end_sec)

        total_time = (end_dt - start_dt).total_seconds()
        # end_dt = start_dt + timedelta(hours=1)

        # print(start_dt)
        # print(end_dt)

        # start_day = end_dt.day
        # start_hour = end_dt.hour
        # start_min = end_dt.minute
        # start_sec = end_dt.second

        # print(start_dt.day)
        # exit()

        # print(float(distance_data["facility_factor"]))

        distance_line = distance_data[
            (distance_data["board"].str.contains("bruno2"))
            # & (distance_data["start"] <= start_dt)
            # & (start_dt <= distance_data["end"])
        ]
        # print(machine)
        oi = distance_line["facility_factor"]
        facility_factor = float(distance_line["facility_factor"])
        distance_attenuation = float(distance_line["Distance attenuation"])

        flux, time_beam_off = get_fluency_flux(
            start_dt=start_dt,
            end_dt=end_dt,
            neutron_count=neutron_count,
            facility_factor=facility_factor,
            distance_attenuation=distance_attenuation,
        )

        fluence = flux * total_time  # 1hour in seconds
        # fluency = flux

        print(start_dt, flux, time_beam_off, fluence, total_time)

    # print(f"in: {csv_file_name}")
    # print(f"out: {csv_out_file_summary}")
    # final_df.to_csv(csv_out_file_summary, index=False, date_format="%Y-%m-%d %H:%M:%S")


#########################################################
#                    Main Thread                        #
#########################################################
if __name__ == "__main__":
    main()
