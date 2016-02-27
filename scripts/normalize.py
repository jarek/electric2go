#!/usr/bin/env python3
# coding=utf-8

from __future__ import print_function
import argparse
import os
import sys

# ask script to look for the electric2go package in one directory up
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from electric2go import files
from electric2go.analysis import cmdline
from electric2go.analysis.normalize import batch_load_data


def process_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('system', type=str,
                        help='system to be used (e.g. car2go, drivenow, ...)')
    parser.add_argument('starting_filename', type=str,
                        help='name of archive of files or the first file')
    parser.add_argument('-st', '--starting-time', type=str,
                        help='optional: if using an archive, first data point '
                             'to process; format YYYY-mm-DD--HH-MM')
    parser.add_argument('-et', '--ending-time', type=str,
                        help='optional: if using an archive, data point '
                             'to stop at; format YYYY-mm-DD--HH-MM')
    parser.add_argument('-step', '--time-step', type=int, default=60,
                        help='each step is TIME_STEP seconds (default 60)')
    parser.add_argument('-i', '--indent', type=int, default=None,
                        help='indent for output JSON (default none)')

    args = parser.parse_args()
    params = vars(args)

    if not os.path.exists(params['starting_filename']):
        sys.exit('file not found: ' + params['starting_filename'])

    if params['starting_time']:
        try:
            params['starting_time'] = files.parse_date(params['starting_time'])
        except ValueError:
            sys.exit('time format not recognized: ' + params['starting_time'])

    if params['ending_time']:
        try:
            params['ending_time'] = files.parse_date(params['ending_time'])
        except ValueError:
            sys.exit('time format not recognized: ' + params['ending_time'])

    try:
        result = batch_load_data(
            params['system'], params['starting_filename'],
            params['starting_time'], params['ending_time'],
            params['time_step'])
    except ValueError as e:
        # raised when an invalid system is encountered
        # or the first data file is invalid
        sys.exit(e)

    if params['ending_time']\
            and params['ending_time'] > result['metadata']['ending_time']:
        print('warning: requested ending_time was {et}, but only found data up to {at}; using {at}'.
              format(et=params['ending_time'], at=result['metadata']['ending_time']),
              file=sys.stderr)

    cmdline.write_json(result, indent=params['indent'])


if __name__ == '__main__':
    process_commandline()
