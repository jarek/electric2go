# coding=utf-8

from datetime import timedelta
import os

from . import cmdline
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

    # add in parkings of which we don't yet know when they finished
    current_positions.extend([unfinished_parkings[vin] for vin in unfinished_parkings
                              if unfinished_parkings[vin]['starting_time'] <= turn])

    if include_trips:
        current_trips = [trip for vin in fin_trips for trip in fin_trips[vin]
                         if trip['ending_time'] == turn]
    else:
        current_trips = None

    return turn, current_positions, current_trips


def build_data_frames(result_dict, include_trips=True):
    # start from the starting time
    turn = result_dict['metadata']['starting_time']

    while turn <= result_dict['metadata']['ending_time']:
        data_frame = build_data_frame(result_dict, turn, include_trips)

        yield data_frame

        turn += timedelta(seconds=result_dict['metadata']['time_step'])


def build_obj(data_frame, parser, result_dict):
    turn, current_positions, _ = data_frame

    def undo_normalize(car_data):
        # undoes normalize.process_data.process_car

        car_data['lat'] = car_data['coords'][0]
        car_data['lng'] = car_data['coords'][1]
        del car_data['coords']

        if 'duration' in car_data:
            del car_data['duration']  # this is added in normalize end_parking

        # add in stuff that doesn't change between data frames,
        # it is stored separately in 'vehicles' key
        car_details = result_dict['vehicles'].get(car_data['vin'], {})
        car_data.update(car_details)

        return car_data

    def roll_out_changing_data(car_data, changing_data):
        if changing_data:
            # find updates to apply, if some are found, apply the latest
            data_updates = [update[1] for update in changing_data if update[0] <= turn]
            if data_updates:
                car_data = parser.put_car_parking_drift(car_data, data_updates[-1])

        return car_data

    # This implicitly assumes that system always returns a list,
    # rather than e.g. a dict.
    # But that seems fine logically, I haven't seen a dict yet.
    # Also that assumption is in other parts of the code,
    # e.g. normalize.process_data where I do "for car in available_cars".

    # Verified manually that the cars-in-a-list assumption held in August 2016 for the following systems:
    # - car2go (no non-car content in the API JSON result)
    # - drivenow (kind of a lot of non-car content, need to analyze if we need to keep any of it)
    # - communauto (marginal non-car content: "{"ExtensionData":{},"UserPosition":{"ExtensionData":{},"Lat":0,"Lon":0},"
    # - evo (marginal non-car content: "{"success":true,"error":false,")
    # - enjoy is broken so I dunno
    # - multicity has that hacky API with lots of stuff so might be annoying to implement. but cars are indeed a list
    # - sharengo (marginal non-car content: "{"status":200,"reason":"",)
    # - translink whole thing is a list so put_cars will just return its param. that works too I guess

    # `car in current_positions` here ultimately comes from a result_dict,
    # which could be still used for other purposes - so dict.copy it first
    # to avoid undo_normalize and roll_out_changing_data creating side-effects
    system_cars = (
        roll_out_changing_data(
            parser.put_car(
                undo_normalize(
                    dict.copy(car)
                )
            ),
            car.get('changing_data', None)
        ) for car in current_positions)

    system_obj = parser.put_cars(list(system_cars), result_dict)  # TODO: otherwise json cannot serialize, lame

    return turn, system_obj


def build_objs(result_dict):
    parser = systems.get_parser(result_dict['metadata']['system'])

    # source files don't include trip info,
    # so tell build_data_frames we don't need that
    data_frames = build_data_frames(result_dict, False)

    # process each data frame and return as generator
    return (build_obj(data_frame, parser, result_dict)
            for data_frame in data_frames)


def write_files(result_dict, location):
    # TODO: depending on how it's being used, this function might not belong here
    city = result_dict['metadata']['city']
    for data_time, data_dict in build_objs(result_dict):
        file_name = files.get_file_name(city, data_time)
        file_path = os.path.join(location, file_name)

        with open(file_path, 'w') as f:
            cmdline.write_json(data_dict, f)
