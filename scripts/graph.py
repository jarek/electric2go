#!/usr/bin/env python3
# coding=utf-8

from __future__ import print_function
import argparse
import os
import sys

# ask script to look for the electric2go package in one directory up
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from electric2go.cars import output_file_name
from electric2go.analysis import cmdline, graph


def process_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-symbol', type=str, default='.',
                        help='matplotlib symbol to indicate vehicles on the images '
                             '(default \'.\', larger \'o\')')
    parser.add_argument('-ap', '--all-positions-image', action='store_true',
                        help='create image of all vehicle positions in the dataset')
    parser.add_argument('-atl', '--all-trips-lines-image', action='store_true',
                        help='create image of all trips in the dataset')
    parser.add_argument('-atp', '--all-trips-points-image', action='store_true',
                        help='create image of all trips in the dataset')

    args = parser.parse_args()
    params = vars(args)

    result_dict = cmdline.read_json()

    if params['all_positions_image']:
        output_file = output_file_name('all_positions', 'png')
        graph.make_positions_graph(result_dict, output_file, params['symbol'])

        print(output_file)

    if params['all_trips_lines_image']:
        output_file = output_file_name('all_trips', 'png')
        graph.make_trips_graph(result_dict, output_file)

        print(output_file)

    if params['all_trips_points_image']:
        output_file = output_file_name('all_trips_points', 'png')
        graph.make_trip_origin_destination_graph(result_dict, output_file, params['symbol'])

        print(output_file)


if __name__ == '__main__':
    process_commandline()
