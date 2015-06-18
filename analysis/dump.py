#!/usr/bin/env python2
# coding=utf-8

import datetime
import json


def format_for_json(trips, tz_offset=0):
    # default JSON serializer doesn't support datetime objects,
    # so I have to manually rewrite them with unicode()

    for trip in trips:
        # adjust timezone if needed
        if tz_offset != 0:
            offset = datetime.timedelta(hours=tz_offset)
            trip['starting_time'] = trip['starting_time'] + offset
            trip['ending_time'] = trip['ending_time'] + offset

        trip['starting_time'] = unicode(trip['starting_time'])
        trip['ending_time'] = unicode(trip['ending_time'])

    return trips


def dump_trips(all_trips, filename, tz_offset):
    trips = format_for_json(all_trips, tz_offset)

    with open(filename, 'w') as f:
        f.write(json.dumps(trips))
