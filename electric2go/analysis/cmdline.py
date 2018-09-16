# coding=utf-8

import sys
from datetime import datetime

# This file will particularly be used with larger JSON files/objects
# so try to get better-performing module first.
# simplejson is usually slightly faster than json running my tests,
# (simplejson=3.8.0, py2.7.8 & py3.4.2)
# so load it if present. If not available, json is fine.
try:
    import simplejson as json
except ImportError:
    import json


def json_serializer(obj):
    # default doesn't serialize dates... tell it to use isoformat()
    # syntax from http://blog.codevariety.com/2012/01/06/python-serializing-dates-datetime-datetime-into-json/
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


def _strptime(t):
    return datetime.strptime(t, "%Y-%m-%dT%H:%M:%S")


def json_deserializer(obj):
    # parse datetimes from JSON we wrote
    for (key, value) in obj.items():

        # json_deserializer is used as an object_hook. That only runs on objects,
        # that is, dicts. We are also storing datetimes as lists in the 'missing'
        # and 'changing_data' keys.
        # List items don't get passed into object_hook so we need to catch it separately. Sucks.
        if key == 'missing':
            datetimes_as_string_list = obj[key]
            obj[key] = [_strptime(t) for t in datetimes_as_string_list]
        elif key == 'changing_data':
            changing_data = obj[key]
            obj[key] = [(_strptime(item[0]), item[1]) for item in changing_data]

        try:
            # this is the format that isoformat outputs
            obj[key] = _strptime(value)
        except (TypeError, ValueError):
            pass

    return obj


def write_json(data, fp=sys.stdout, indent=0):
    json.dump(data, fp=fp, default=json_serializer, indent=indent)


def read_json(fp=sys.stdin):
    return json.load(fp=fp, object_hook=json_deserializer)
