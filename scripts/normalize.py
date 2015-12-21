#!/usr/bin/env python3
# coding=utf-8

from __future__ import print_function
import argparse
import os
import sys
import tarfile

# ask script to look for the electric2go package in one directory up
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from electric2go import cars
from electric2go.analysis import cmdline
from electric2go.analysis.normalize import batch_load_data, get_city_and_time_from_filename


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

    json_indent = args.indent
    filename = args.starting_filename

    if not os.path.exists(filename):
        sys.exit('file not found: ' + filename)

    # Handle the following cases:
    # - filename being like "car2go-archives/wien_2015-06-19.tgz" <- archive
    # - filename being like "car2go-archives/wien_2015-06-19--04-00" <- first of many files

    try:
        city, time_in_filename = get_city_and_time_from_filename(filename)

        if params['starting_time']:
            params['starting_time'] = cars.parse_date(params['starting_time'])
        else:
            params['starting_time'] = time_in_filename
    except ValueError:
        sys.exit('time format not recognized: ' + params['starting_time'])

    if params['ending_time']:
        try:
            # parse ending time
            params['ending_time'] = cars.parse_date(params['ending_time'])
        except ValueError:
            sys.exit('time format not recognized: ' + params['ending_time'])

    if tarfile.is_tarfile(filename):
        location = filename
        city = os.path.split(city.lower())[1]
    else:
        location, city = os.path.split(city.lower())

    params['city'] = city
    params['location'] = location

    del params['starting_filename']
    del params['indent']

    result = batch_load_data(**params)

    if params['ending_time']\
            and params['ending_time'] > result['metadata']['ending_time']:
        print('warning: requested ending_time was {et}, but only found data up to {at}; using {at}'.
              format(et=params['ending_time'], at=result['metadata']['ending_time']),
              file=sys.stderr)

    cmdline.write_json(result, indent=json_indent)


if __name__ == '__main__':
    process_commandline()
