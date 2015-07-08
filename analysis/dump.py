#!/usr/bin/env python2
# coding=utf-8

import datetime


def trips_offset_tz(trips, tz_offset):
    for trip in trips:
        offset = datetime.timedelta(hours=tz_offset)
        trip['starting_time'] = trip['starting_time'] + offset
        trip['ending_time'] = trip['ending_time'] + offset

    return trips


def json_serializer(obj):
    # default doesn't serialize dates... tell it to use isoformat()
    # syntax from http://blog.codevariety.com/2012/01/06/python-serializing-dates-datetime-datetime-into-json/
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


def json_deserializer(obj):
    # parse datetimes from JSON we wrote
    for (key, value) in obj.items():
        if isinstance(value, basestring):
            try:
                # this is the format that isoformat outputs
                obj[key] = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            except:
                pass

    return obj
