# coding=utf-8

from datetime import timedelta


# This is basically the inverse of normalize.py
# - it generates per-minute / per-moment state
# from a result_dict.


def build_data_frame(result_dict, turn, include_trips=False):
    # shorter variable names for easier access
    fin_parkings = result_dict['finished_parkings']
    fin_trips = result_dict['finished_trips']
    unfinished_parkings = result_dict['unfinished_parkings']

    # flatteb list
    finished_parkings = [item for vin in fin_parkings for item in fin_parkings[vin]]

    # filter list
    current_positions = [p for p in finished_parkings
                         if p['starting_time'] <= turn <= p['ending_time']]

    # add in parkings that we don't know when they finished
    current_positions.extend([unfinished_parkings[vin] for vin in unfinished_parkings
                              if unfinished_parkings[vin]['starting_time'] <= turn])

    if include_trips:
        finished_trips = [trip for vin in fin_trips for trip in fin_trips[vin]]
        current_trips = [p for p in finished_trips
                         if p['ending_time'] == turn]
    else:
        current_trips = None

    data_frame = (current_positions, current_trips)
    return data_frame


def build_data_frames(result_dict):
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

        current_positions, current_trips = build_data_frame(result_dict, turn, True)

        data_frame = (index, turn, current_positions, current_trips)
        yield data_frame

        index += 1
        turn += timedelta(seconds=result_dict['metadata']['time_step'])


def build_files(result_dict):
    pass


def write_files(result_dict):
    pass