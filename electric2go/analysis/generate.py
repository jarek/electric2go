# coding=utf-8

from collections import defaultdict
from datetime import timedelta
import os

from . import cmdline, normalize
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
                         if trip['end']['time'] == turn]
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
    # note: this isn't a deep copy, so nested dicts as seen for e.g. drivenow might break :(
    system_cars = (
        parser.put_car(
            roll_out_changing_data(
                undo_normalize(
                    dict.copy(car)
                ),
                car.get('changing_data', None)
            )
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
        # If file was missing in the original, don't write it out.
        # Strictly speaking, this doesn't always perfectly recreate the original files.
        # For instance, if the server returned an "<html><h1>503 Service Unavailable</h1></html>" response,
        # this will be treated as unparseable, recorded as missing, and its contents information not saved.
        # When generated, the file will not be written at all.
        # But I am already not recreating the originals *perfectly* due to being unable
        # to preserve list order, and recreating error data isn't high on my priority list...
        if data_time in result_dict['metadata']['missing']:
            continue

        file_name = files.get_file_name(city, data_time)
        file_path = os.path.join(location, file_name)

        # TODO: it would be good to parallelize this, but a quick attempt in f39bb45c5b
        # resulted in test failures due to incorrect data being written... hrm
        with open(file_path, 'w') as f:
            cmdline.write_json(data_dict, f)


# TODO: this duplicates tests.py GenerateTest except with worse error reporting - factor out somehow?
def compare_files(result_dict, expected_location, actual_location):
    metadata = result_dict['metadata']
    return compare_files_for_system(metadata['system'], metadata['city'],
                                    expected_location, actual_location,
                                    metadata['starting_time'],
                                    metadata['ending_time'],
                                    metadata['time_step'])


def compare_files_for_system(system, city, expected_location, actual_location,
                             start_time, end_time, time_step):
    # Name where files have been generated might be a tempdir name
    # like '/tmp/tmp25l2ba19', while Electric2goDataArchive expects
    # a trailing slash if not a file name - so add a trailing slash.
    actual_location = os.path.join(actual_location, '')

    expected_data_archive = normalize.Electric2goDataArchive(city, expected_location)
    actual_data_archive = normalize.Electric2goDataArchive(city, actual_location)

    differing_vins = defaultdict(list)
    differing_keys = defaultdict(list)
    differing_remainder_keys = defaultdict(list)

    comparison_time = start_time
    while comparison_time <= end_time:
        (step_diff_vins, step_diff_keys, step_remainder_keys) = _compare_system_independent(
            system, expected_data_archive, actual_data_archive, comparison_time)

        for vin in step_diff_vins:
            differing_vins[vin].append(comparison_time)

        for key in step_diff_keys:
            differing_keys[key].append(comparison_time)

        for key in step_remainder_keys:
            differing_remainder_keys[key].append(comparison_time)

        comparison_time += timedelta(seconds=time_step)

    if len(differing_vins):
        print("======================")
        print("=== differing VINs: {}".format(differing_vins))

    if len(differing_keys):
        print("======================")
        print("=== differing keys for cars: {}".format(differing_keys))

    if len(differing_remainder_keys):
        print("======================")
        print("=== differing keys in remainder info: {}".format(differing_remainder_keys))

    return True


def _compare_system_independent(system, expected_data_archive, actual_data_archive, comparison_time):
    parser = systems.get_parser(system)

    expected_file = expected_data_archive.load_data_point(comparison_time)

    actual_file = actual_data_archive.load_data_point(comparison_time)

    # load_data_point can return False when the file is missing or malformed.
    # When that happens, expect it on both archives.
    if expected_file is False:
        if actual_file is False:
            print("expected_file and actual_file are both False")
            return set(), set(), set()
        else:
            return set(), set(), set("expected_file is False, but actual_file is not")

    # test cars equivalency. we have to do it separately because
    # it comes from API as a list, but we don't store the list order.
    expected_cars = parser.get_cars_dict(expected_file)
    actual_cars = parser.get_cars_dict(actual_file)

    differing_vins = set()
    differing_keys = set()

    # test for equivalency of cars
    if expected_cars != actual_cars:
        print("{}: cars are not equiv".format(comparison_time))
        for vin, car in expected_cars.items():
            if car != actual_cars[vin]:
                print(vin + " is the first offender")
                differing_vins.add(vin)
                for key in car:
                    if car[key] != actual_cars[vin][key]:
                        print(key + ": in expected: " + repr(car[key]) + ", in actual: " + repr(actual_cars[vin][key]))
                        differing_keys.add(key)
                # return False

    # test exact equivalency of everything but the cars list
    expected_remainder = parser.get_everything_except_cars(expected_file)
    actual_remainder = parser.get_everything_except_cars(actual_file)

    differing_remainder_keys = set()

    if expected_remainder != actual_remainder:
        if expected_remainder.get('code', '') == 500:
            # this happens sometimes, ignore it
            print("{}: expected_remainder was a 500 JSON, returning valid".format(comparison_time))
            return differing_vins, differing_keys, differing_remainder_keys

        print("{}: remainders are wrong".format(comparison_time))
        for key, value in expected_remainder.items():
            if key not in actual_remainder:
                print("key missing from generated: {}".format(key))
                print("!!!!!!!!!!!!!!!!!!!!!!!!!")
                print("!!!!!!!!!!!!!!!!!!! unrecognized key, pay attention!!")
                print("!!!!!!!!!!!!!!!!!!!!!!!!!")
                differing_remainder_keys.add(key)
                # return False

            elif value != actual_remainder[key]:
                print(key + ": in expected: " + repr(value) + ", in actual: " + repr(actual_remainder[key]))
                differing_remainder_keys.add(key)
                if not (system == "drivenow" and key in ("emergencyStatus", "marketingMessage", "message")):
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!")
                    print("!!!!!!!!!!!!!!!!!!! unrecognized key, pay attention!!")
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!")
                # return False

    return differing_vins, differing_keys, differing_remainder_keys
