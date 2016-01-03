#!/usr/bin/env python3
# coding=utf-8

from __future__ import print_function
import argparse
import os
import sys

# ask script to look for the electric2go package in one directory up
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from electric2go.analysis.process import batch_process


def process_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-tz', '--tz-offset', type=int, default=0,
                        help='offset times by TZ_OFFSET hours')
    parser.add_argument('-v', '--video', action='store_true',
                        help='generate minute-by-minute images for animating into a video')
    parser.add_argument('-lines', '--show-move-lines', action='store_true',
                        help='show lines indicating vehicles\' trips')
    parser.add_argument('-d', '--distance', type=float, default=False,
                        help='mark distance of DISTANCE meters from nearest car on map')
    parser.add_argument('-speeds', '--show_speeds', action='store_true',
                        help='indicate vehicles\' speeds in addition to locations')
    parser.add_argument('-symbol', type=str, default='.',
                        help='matplotlib symbol to indicate vehicles on the images '
                             '(default \'.\', larger \'o\')')
    parser.add_argument('-s', '--stats', action='store_true',
                        help='generate some basic statistics about carshare use')
    parser.add_argument('-ap', '--all-positions-image', type=str, default=False,
                        help='create image of all vehicle positions in the dataset and save to ALL_POSITIONS_IMAGE')
    parser.add_argument('-atl', '--all-trips-lines-image', type=str, default=False,
                        help='create image of all trips in the dataset and save to ALL_TRIPS_LINES_IMAGE')
    parser.add_argument('-atp', '--all-trips-points-image', type=str, default=False,
                        help='create image of all trips in the dataset and save to ALL_TRIPS_POINTS_IMAGE')

    args = parser.parse_args()
    params = vars(args)

    batch_process(**params)


if __name__ == '__main__':
    process_commandline()
