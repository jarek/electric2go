#!/usr/bin/env python3
# coding=utf-8

import argparse
from random import sample

import cmdline


def by_vehicle(result_dict, find_by):
    """
    :param find_by: accepts VINs, "random", "most_trips", "most_distance", and "most_duration"
    :return: result_dict only containing data for the requested car
    """

    all_known_vins = set()
    all_known_vins.update(result_dict['unfinished_trips'].keys())
    all_known_vins.update(result_dict['finished_trips'].keys())
    all_known_vins.update(result_dict['unfinished_parkings'].keys())
    all_known_vins.update(result_dict['finished_parkings'].keys())
    all_known_vins.update(result_dict['unstarted_trips'].keys())

    all_trips_by_vin = result_dict['finished_trips']

    vin = find_by  # allow finding by passing in VIN verbatim

    if find_by == 'random':
        vin = sample(all_known_vins, 1)[0]
    elif find_by == 'most_trips':
        # pick the vehicle with most trips. in case of tie, pick first one
        vin = max(all_trips_by_vin,
                  key=lambda v: len(all_trips_by_vin[v]))
    elif find_by == 'most_distance':
        vin = max(all_trips_by_vin,
                  key=lambda v: sum(t['distance'] for t in all_trips_by_vin[v]))
    elif find_by == 'most_duration':
        vin = max(all_trips_by_vin,
                  key=lambda v: sum(t['duration'] for t in all_trips_by_vin[v]))

    if vin not in all_trips_by_vin:
        raise KeyError("VIN %s not found in result_dict" % vin)

    vin_to_find = vin

    result_dict['finished_trips'] = {k: v for k, v in result_dict['finished_trips'].items() if k == vin_to_find}
    result_dict['unfinished_trips'] = {k: v for k, v in result_dict['unfinished_trips'].items() if k == vin_to_find}
    result_dict['finished_parkings'] = {k: v for k, v in result_dict['finished_parkings'].items() if k == vin_to_find}
    result_dict['unfinished_parkings'] = {k: v for k, v in result_dict['unfinished_parkings'].items() if k == vin_to_find}
    result_dict['unstarted_trips'] = {k: v for k, v in result_dict['unstarted_trips'].items() if k == vin_to_find}

    return result_dict


def process_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--by-vehicle', type=str, default=False,
                        help='filter all results to only include data for one vehicle; '
                             'accepts VINs, "random", "most_trips", "most_distance", and "most_duration".')

    args = parser.parse_args()

    input_dict = cmdline.read_json()

    # TODO: add more filters, like filtering by timeframe, latlng, etc
    # though it might be easier to provide a harness and have the filter functions be per-analysis-project
    # - at least for now until I figure out what the most used filters are

    result_dict = by_vehicle(input_dict, args.by_vehicle)

    cmdline.write_json(result_dict)


if __name__ == '__main__':
    process_commandline()
