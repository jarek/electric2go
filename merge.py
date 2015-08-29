#!/usr/bin/env python3
# coding=utf-8

from __future__ import print_function
import argparse
from datetime import timedelta

import cmdline
import normalize


def merge_two_dicts(one, two):
    """
    Merge two result_dicts:
    - second dict's unstarted_trips are merged with first dict's unfinished_parkings and unfinished_trips as appropriate
    - key merge on finished_trips, appending
    - key merge on finished_parkings, appending
    - merge metadata:
        - system, city, time_step stay the same
        - missing from second is appended to missing from first
        - starting_time from first dict
        - ending_time from second dict
    :param one: first result_dict. if None, `two` is returned immediately
    :param two: second result_dict
    :return: merged result_dict
    """

    if not one:
        # first iteration so `one` doesn't have an existing result yet,
        # just return the `two`
        return two

    def merge(one_sub, two_sub, key):
        for vin_sub in two_sub[key]:
            if vin_sub in one_sub[key]:
                one_sub[key][vin_sub].extend(two_sub[key][vin_sub])
            else:
                one_sub[key][vin_sub] = two_sub[key][vin_sub]

        return one_sub

    one_ending_time = one['metadata']['ending_time']
    two_starting_time = two['metadata']['starting_time']

    time_step = timedelta(seconds=one['metadata']['time_step'])
    should_be_second_starting_time = one_ending_time + time_step
    if two_starting_time != should_be_second_starting_time:
        raise ValueError("Files don't appear to be in order. ending_time and starting_time "
                         "must be consecutive, but instead they are {} and {}"
                         .format(one_ending_time, two_starting_time))

    for vin in two['unstarted_trips']:
        unstarted_trip = two['unstarted_trips'][vin]

        if (vin in one['unfinished_parkings']
                and unstarted_trip['ending_time'] == two_starting_time
                and one['unfinished_parkings'][vin]['coords'][0] == unstarted_trip['to'][0]
                and one['unfinished_parkings'][vin]['coords'][1] == unstarted_trip['to'][1]):

            # most common case, cars that were parked over the break

            if (vin in two['finished_parkings']
                    and two['finished_parkings'][vin][0]['starting_time'] == two_starting_time):

                # merge unfinished parking with first one in two['finished_parkings']

                parking_info = two['finished_parkings'][vin][0]
                parking_info_start = one['unfinished_parkings'][vin]

                parking_info['starting_time'] = parking_info_start['starting_time']
                parking_info = normalize.calculate_parking(parking_info)

                two['finished_parkings'][vin][0] = parking_info
                one['unfinished_parkings'].pop(vin)  # delete

            else:
                # Cars were parked over the break but then didn't move at all the next day.
                # Keep it as unfinished parking, without deleting it from the list.
                # Because of code later on that updates one['unfinished_parkings'] with
                # two['unfinished_parkings'], update the latter, giving it correct starting_time.

                two['unfinished_parkings'][vin] = one['unfinished_parkings'][vin]

        elif vin in one['unfinished_trips']:
            # trip spanning the break, merge the information from unfinished_trips and unstarted_trips
            # then append to finished_trips

            trip_data = one['unfinished_trips'][vin]
            trip_data.update(unstarted_trip)

            trip_data = normalize.calculate_trip(trip_data)

            if vin in one['finished_trips']:
                one['finished_trips'][vin].append(trip_data)
            else:
                one['finished_trips'][vin] = [trip_data]

            one['unfinished_trips'].pop(vin)  # delete

        else:
            # could be a brand new car entering service, log it
            one['unstarted_trips'][vin] = unstarted_trip

    one = merge(one, two, 'finished_trips')
    one = merge(one, two, 'finished_parkings')

    one['unfinished_parkings'].update(two['unfinished_parkings'])
    one['unfinished_trips'].update(two['unfinished_trips'])

    one['metadata']['missing'].extend(two['metadata']['missing'])

    one['metadata']['ending_time'] = two['metadata']['ending_time']

    return one


def merge_all_dicts(dicts):
    result_dict = None
    for loaded_dict in dicts:
        result_dict = merge_two_dicts(result_dict, loaded_dict)

    return result_dict


def merge_all_files(files):
    file_objs = (cmdline.read_json(fp=open(file_to_load))
                 for file_to_load in files)

    return merge_all_dicts(file_objs)


def process_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', type=str, nargs='+',
                        help='files to merge, must be in order')
    args = parser.parse_args()

    result_dict = merge_all_files(args.files)

    cmdline.write_json(result_dict)


if __name__ == '__main__':
    process_commandline()
