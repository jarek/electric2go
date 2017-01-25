#!/usr/bin/env python3
# coding=utf-8

from __future__ import print_function
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
    result_dict = cmdline.read_json()

    generate.write_files(result_dict, '')


if __name__ == '__main__':
    process_commandline()
