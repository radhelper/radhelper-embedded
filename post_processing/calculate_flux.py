#!/usr/bin/env python3
from datetime import datetime
import numpy as np
import pandas as pd
import sys
import os


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


# def filter_beam_off(neutron_count: np.array, beam_off_time: float):
def parse_line(line):
    """Parse a line from the file and return the date, time and observation"""
    parts = line.split("\t")
    date_str, time_str, observation = parts
    dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
    return dt, observation.strip()


def calculate_open_periods(filename):
    """Calculate the time windows when the shutter is open"""
    with open(filename, "r") as file:
        lines = file.readlines()[1:]  # Skip the header line

    open_time = None
    periods = []

    for line in lines:
        dt, observation = parse_line(line)

        if "open" in observation.lower() and open_time is None:
            open_time = dt
        elif "close" in observation.lower() and open_time is not None:
            close_time = dt
            period = (open_time, close_time)
            periods.append(period)
            open_time = None

    return periods
