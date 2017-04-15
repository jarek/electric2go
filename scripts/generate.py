#!/usr/bin/env python3
# coding=utf-8

from __future__ import print_function
import argparse
import os
import sys

# ask script to look for the electric2go package in one directory up
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from electric2go.analysis import cmdline, generate


# This does the inverse of normalize: given a result_dict on stdin,
# generate files as they would have come out of the system's API.

# This should be used rarely, mostly useful to generate test data
# or test that normalization can be fully undone.

# TODO: include a call to this in tests (similar to test_merge_pipeline)


def process_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--check', type=str,
                        help='optional: verify that the generated files'
                             'has the same contents as the CHECK archive')
    args = parser.parse_args()

    result_dict = cmdline.read_json()

    target_directory = ''

    generate.write_files(result_dict, target_directory)

    if args.check:
        equal = generate.compare_files(result_dict, args.check, target_directory)
        if not equal:
            raise RuntimeError('Generated file is not the same as original!')


if __name__ == '__main__':
    process_commandline()
