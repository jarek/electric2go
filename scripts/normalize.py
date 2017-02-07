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

    if not os.path.exists(args.starting_filename):
        sys.exit('file not found: ' + args.starting_filename)

    # TODO: also support more standard YYYY-mm-DDTHH-MM (ISO 8601)
    # in addition to YYYY-mm-DD--HH-MM when parsing dates here.
    # I guess changing the file naming to match would be a bit of a big
    # and breaking change... hmm.

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

    try:
        result = batch_load_data(args.system, args.starting_filename,
                                 args.starting_time, args.ending_time,
                                 args.time_step)
    except ValueError as e:
        # raised when an invalid system is encountered
        # or the first data file is invalid
        sys.exit(e)

    if args.ending_time and args.ending_time > result['metadata']['ending_time']:
        print('warning: requested ending_time was {et}, but only found data up to {at}; using {at}'.
              format(et=args.ending_time, at=result['metadata']['ending_time']),
              file=sys.stderr)

    cmdline.write_json(result, indent=args.indent)


if __name__ == '__main__':
    process_commandline()
