#!/usr/bin/env python3
# coding=utf-8

from __future__ import print_function
import datetime
import os
import sys

# ask script to look for the electric2go package in one directory up
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from electric2go.download import save


def process_commandline():
    if len(sys.argv) < 3:
        sys.exit('!!! must specify system and city to download (or system and "all")')

    requested_system = sys.argv[1].lower()
    requested_city = sys.argv[2].lower()

    if len(sys.argv) > 3:
        requested_archive = (sys.argv[3].lower() == 'archive')
    else:
        requested_archive = False

    t, failures = save(requested_system, requested_city, should_archive=requested_archive)

    end_time = datetime.datetime.utcnow()

    print('{timestamp} downloading {system} {city}, finished {end}'.format(
        timestamp=str(t), system=requested_system, city=requested_city, end=end_time))

    for failed in failures:
        message = '!!! could not download or save information for system {system} city {city}'
        print(message.format(system=failed[0], city=failed[1]))


if __name__ == '__main__':
    process_commandline()
