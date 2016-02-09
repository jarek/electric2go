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

    # The condition of `p['starting_time'] <= turn <= p['ending_time']`
    # (with the two less-than-or-equal) in the statement to get
    # current_positions is correct.

    # I was initially afraid it was wrong because parking periods
    # are defined in normalize.process_data as follows:
    #   "A parking period starts on data_time and ends on prev_data_time."
    # and so I thought this had to be `turn < p['ending_time']`

    # But actually the equals on both ends is fine. process_data does the
    # logical filtering as to when a parking starts and ends. With this,
    # in process_data output, cars are still available when
    # `turn == p['ending_time']`. Trying to do `turn < p['ending_time']`
    # would be double-filtering.
    # (Confirmed with actually looking at source data.)

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
        current_positions, current_trips = build_data_frame(result_dict, turn, include_trips)

        data_frame = (index, turn, current_positions, current_trips)
        yield data_frame

        index += 1
        turn += timedelta(seconds=result_dict['metadata']['time_step'])


def build_json(data_frame, write_car_data, write_cars_to_json):
    _, turn, current_positions, _ = data_frame

    formatted_cars = (write_car_data(car) for car in current_positions)

    formatted_json = write_cars_to_json(formatted_cars)

    return turn, formatted_json


def build_jsons(result_dict):
    parse_module = systems.get_parser(result_dict['metadata']['system'])

    write_car_data = getattr(parse_module, 'write_car_data')
    write_cars_to_json = getattr(parse_module, 'write_cars_to_json')

    # source files don't include trip info,
    # so tell build_data_frames we don't need that
    data_frames = build_data_frames(result_dict, False)

    # process each data frame and return as generator
    return (build_json(data_frame, write_car_data, write_cars_to_json)
            for data_frame in data_frames)


def write_files(result_dict):
    city = result_dict['metadata']['city']
    for data_time, data_dict in build_jsons(result_dict):
        file_name = files.get_file_name(city, data_time)
        # TODO: output dir? as param?
        with open(file_name, 'w') as f:
            json.dump(data_dict, f)
