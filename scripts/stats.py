#!/usr/bin/env python3
# coding=utf-8

from __future__ import print_function
import argparse
import os
import sys

# ask script to look for the electric2go package in one directory up
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from electric2go.cars import output_file_name
from electric2go.analysis import cmdline, stats


def process_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-tz', '--tz-offset', type=int, default=0,
                        help='offset times when days are split by TZ_OFFSET hours')

    args = parser.parse_args()
    params = vars(args)

    result_dict = cmdline.read_json()

    output_file = output_file_name('stats', 'csv')

    stats.stats(result_dict, output_file, params['tz_offset'])

    print(output_file)  # provide output name for easier reuse


if __name__ == '__main__':
    process_commandline()
