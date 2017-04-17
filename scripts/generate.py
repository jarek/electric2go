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


def process_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--check', type=str,
                        help='optional: verify that the generated files '
                             'have the same contents as the CHECK archive')
    parser.add_argument('--check-only', action='store_true',
                        help='don\'t generate the files before checking; '
                             'can be useful to check files already generated')
    args = parser.parse_args()

    if args.check_only and not args.check:
        raise RuntimeError('--check-only can only be used with --check')

    result_dict = cmdline.read_json()

    # use the shell's current working directory
    target_directory = ''

    if not args.check_only:
        generate.write_files(result_dict, target_directory)

    if args.check:
        try:
            generate.compare_files(result_dict, args.check, target_directory)
        except AssertionError as e:
            raise RuntimeError('Generated file at {} is not the same as original!'.format(e))


if __name__ == '__main__':
    process_commandline()
