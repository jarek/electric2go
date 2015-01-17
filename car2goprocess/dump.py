#!/usr/bin/env python2
# coding=utf-8

import datetime
import json


def format_for_json(trips, time_offset=0):
    # default JSON serializer doesn't support datetime objects,
    # so I have to manually rewrite them with unicode()

    for trip in trips:
        # adjust timezone if needed
        if time_offset != 0:
            offset = datetime.timedelta(hours=time_offset)
            trip['starting_time'] = trip['starting_time'] + offset
            trip['ending_time'] = trip['ending_time'] + offset

        trip['starting_time'] = unicode(trip['starting_time'])
        trip['ending_time'] = unicode(trip['ending_time'])

    return trips

def dump_trips(all_trips, filename, time_offset):
    # TODO: allow filtering the data by timeframe, origins

    # data is organized by vehicle (with VIN as the key).
    # for now just dump all trips

    trips = format_for_json(all_trips, time_offset)

    with open(filename, 'w') as f:
        f.write(json.dumps(trips))

def dump_vehicle(all_trips_by_vin, vin, time_offset):
    #  dump of trace results by vehicle's VIN

    trips = format_for_json(all_trips_by_vin[vin], time_offset)

    filename = vin + '_trips.json'

    with open(filename, 'w') as f:
        f.write(json.dumps(trips))

