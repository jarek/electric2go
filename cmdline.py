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


def json_deserializer(obj):
    # parse datetimes from JSON we wrote
    for (key, value) in obj.items():
        try:
            # this is the format that isoformat outputs
            obj[key] = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
        except (TypeError, ValueError):
            pass

    return obj


def write_json(data, fp=sys.stdout, indent=None):
    json.dump(data, fp=fp, default=json_serializer, indent=indent)


def read_json(fp=sys.stdin):
    return json.load(fp=fp, object_hook=json_deserializer)
