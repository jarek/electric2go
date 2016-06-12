#!/usr/bin/env python3
# coding=utf-8

from __future__ import print_function
import argparse
import os
import sys

from tqdm import tqdm

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

    result_dict = cmdline.read_json()

    metadata = result_dict['metadata']

    output_filename_prefix = output_file_name(metadata['city'])

    images_generator = video.make_video_frames(
        result_dict, output_filename_prefix,
        args.distance, args.trips, args.speeds,
        args.symbol, args.tz_offset)

    # evaluate the generator to actually generate the images;
    # use tqdm to display a progress bar
    exp_timespan = metadata['ending_time'] - metadata['starting_time']
    exp_frames = exp_timespan.total_seconds() / metadata['time_step']
    generated_images = list(tqdm(images_generator,
                                 total=exp_frames, leave=False))

    # print animation information
    animate_command_text = video.make_animate_command(
        result_dict, output_filename_prefix, len(generated_images))
    print('\nto animate:')
    print(animate_command_text)


if __name__ == '__main__':
    process_commandline()
