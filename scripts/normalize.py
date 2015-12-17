#!/usr/bin/env python3
# coding=utf-8

from __future__ import print_function
import argparse
import os
import sys
from datetime import datetime
import tarfile

# ask script to look for the electric2go package in one directory up
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from electric2go.analysis import cmdline
from electric2go.analysis.normalize import batch_load_data


def process_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-debug', action='store_true',
                        help='print extra debug and timing messages to stderr')
    parser.add_argument('system', type=str,
                        help='system to be used (e.g. car2go, drivenow, ...)')
    parser.add_argument('starting_filename', type=str,
                        help='name of archive of files or the first file')
    parser.add_argument('-st', '--starting-time', type=str,
                        help='if using an archive, optional first data point '
                             'to process; format YYYY-mm-DD--HH-MM')
    parser.add_argument('-step', '--time-step', type=int, default=60,
                        help='each step is TIME_STEP seconds (default 60)')
    parser.add_argument('-max', '--max-steps', type=int, default=44647,
                        help='limit maximum amount of TIME_STEPs to process '
                             '(default 44647 = 1440 * 31)')
    parser.add_argument('-skip', '--max-skip', type=int, default=3,
                        help='amount of missing or malformed sequential '
                             'steps to try to work around (default 3; '
                             'specify 0 to work only on data provided)')
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

    city, leftover = filename.rsplit('_', 1)

    if not params['starting_time']:
        # don't use splitext so we correctly handle filenames like wien_2015-06-19.tar.gz
        parts = leftover.split('.', 1)

        if len(parts) == 2 and not parts[0].endswith('--00-00'):
            # replace file extension with 00:00 if needed
            leftover = leftover.replace('.' + parts[1], '--00-00')

        params['starting_time'] = leftover

    try:
        # parse out starting time
        params['starting_time'] = datetime.strptime(params['starting_time'],
                                                    '%Y-%m-%d--%H-%M')
    except ValueError:
        sys.exit('time format not recognized: ' + params['starting_time'])

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

    cmdline.write_json(result, indent=json_indent)


if __name__ == '__main__':
    process_commandline()
