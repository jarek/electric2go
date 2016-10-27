#!/usr/bin/env python3
# coding=utf-8

from __future__ import print_function
import argparse
import os
import sys

# ask script to look for the electric2go package in one directory up
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from electric2go import files
from electric2go.analysis import cmdline, generate


# TODO: this should perform the inverse of generate:
# given a result_dict on stdin, generate files as they would have come out of the corresponding API.
# command-line options could be location, starting/ending time to trim result_dict to, maybe indent

# this would be used rarely, mostly to generate test data. maybe it doesn't need to be a separate file
# in /scripts/, only a class in tests.py invoked when needed?


def process_commandline():
    parser = argparse.ArgumentParser()
    # TODO: param for location? or just always have it run in current dir maybe
    parser.add_argument('-st', '--starting-time', type=str,
                        help='optional: if using an archive, first data point '
                             'to process; format YYYY-mm-DD--HH-MM')
    parser.add_argument('-et', '--ending-time', type=str,
                        help='optional: if using an archive, data point '
                             'to stop at; format YYYY-mm-DD--HH-MM')
    parser.add_argument('-i', '--indent', type=int, default=None,
                        help='indent for output JSON (default none)')

    args = parser.parse_args()

    if args.starting_time:
        try:
            args.starting_time = files.parse_date(args.starting_time)
        except ValueError:
            sys.exit('time format not recognized: ' + args.starting_time)

    if args.ending_time:
        try:
            args.ending_time = files.parse_date(args.ending_time)
        except ValueError:
            sys.exit('time format not recognized: ' + args.ending_time)

    result_dict = cmdline.read_json()

    generate.write_files(result_dict, '')


if __name__ == '__main__':
    process_commandline()
