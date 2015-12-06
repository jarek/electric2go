#!/usr/bin/env python3
# coding=utf-8

from __future__ import print_function
import argparse
import os
import sys

# ask script to look for the electric2go package in one directory up
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from electric2go.analysis import cmdline
from electric2go.analysis.merge import merge_all_files


def process_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', type=str, nargs='+',
                        help='files to merge, must be in order')
    args = parser.parse_args()

    result_dict = merge_all_files(args.files)

    cmdline.write_json(result_dict)


if __name__ == '__main__':
    process_commandline()
