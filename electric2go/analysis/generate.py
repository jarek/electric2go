# coding=utf-8

from datetime import timedelta

import json
from .. import files, systems


# This is basically the inverse of normalize.py
# - it generates per-minute / per-moment state
# from a result_dict.


def build_data_frame(result_dict, turn, include_trips):
    # shorter variable names for easier access
    fin_parkings = result_dict['finished_parkings']
    fin_trips = result_dict['finished_trips']
    unfinished_parkings = result_dict['unfinished_parkings']

    # flatten and filter parking list
    current_positions = [p for vin in fin_parkings for p in fin_parkings[vin]
                         if p['starting_time'] <= turn <= p['ending_time']]

    # add in parkings that we don't know when they finished
    current_positions.extend([unfinished_parkings[vin] for vin in unfinished_parkings
                              if unfinished_parkings[vin]['starting_time'] <= turn])

    if include_trips:
        current_trips = [trip for vin in fin_trips for trip in fin_trips[vin]
                         if trip['ending_time'] == turn]
    else:
        current_trips = None

    return current_positions, current_trips


def build_data_frames(result_dict, include_trips=True):
    # start from the starting time
    turn = result_dict['metadata']['starting_time']
    index = 0

    while turn <= result_dict['metadata']['ending_time']:
        # The condition of `p['starting_time'] <= turn <= p['ending_time']`
        # (with the two less-than-or-equal) in the statement to get
        # current_positions is correct.

        # I was initially afraid it was wrong because parking periods
        # are defined in process_data as follows:
        #   "A parking period starts on data_time and ends on prev_data_time."
        # and so I thought this had to be `turn < p['ending_time']`

        # But actually the equals on both ends is fine. process_data does the
        # logical filtering as to when a parking starts and ends. With this,
        # in process_data output, cars are still available when
        # `turn == p['ending_time']`. Trying to do `turn < p['ending_time']`
        # would be double-filtering.
        # (Confirmed with actually looking at source data.)

        current_positions, current_trips = build_data_frame(result_dict, turn, include_trips)

        data_frame = (index, turn, current_positions, current_trips)
        yield data_frame

        index += 1
        turn += timedelta(seconds=result_dict['metadata']['time_step'])
