#!/usr/bin/env python3
# coding=utf-8

import argparse
import os
import sys

# ask script to look for the electric2go package in one directory up
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from electric2go.analysis import cmdline
from electric2go.analysis.filter import by_vehicle


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
