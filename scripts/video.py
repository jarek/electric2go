#!/usr/bin/env python3
# coding=utf-8

from __future__ import print_function
import argparse
import os
import sys

# ask script to look for the electric2go package in one directory up
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from electric2go import output_file_name
from electric2go.analysis import cmdline, video


def process_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-tz', '--tz-offset', type=float, default=0,
                        help='offset times by TZ_OFFSET hours')
    parser.add_argument('-d', '--distance', type=float, default=False,
                        help='highlight DISTANCE meters around each car on map')
    parser.add_argument('--trips', action='store_true',
                        help='show lines indicating vehicles\' trips')
    parser.add_argument('--speeds', action='store_true',
                        help='show vehicles\' speeds in addition to locations')
    parser.add_argument('--symbol', type=str, default='.',
                        help='matplotlib symbol to indicate vehicles on the images' +
                             ' (default \'.\', larger \'o\')')

    args = parser.parse_args()
    params = vars(args)

    result_dict = cmdline.read_json()

    output_filename_prefix = output_file_name(result_dict['metadata']['city'])

    animate_command_text, generated_images = video.make_video_frames(
        result_dict, output_filename_prefix,
        params['distance'], params['trips'], params['speeds'],
        params['symbol'], params['tz_offset'])

    # print animation information
    print('\nto animate:')
    print(animate_command_text)


if __name__ == '__main__':
    process_commandline()