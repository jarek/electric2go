#!/usr/bin/env python2
# coding=utf-8

import json


def format_for_json(trips):
    # default JSON serializer doesn't support datetime objects, bleh
    for trip in trips:
        trip['starting_time'] = unicode(trip['starting_time'])
        trip['ending_time'] = unicode(trip['ending_time'])

    # TODO: when dumping trip data, we should respect 'tz' param 
    # if it was provided and adjust timestamps accordingly

    return trips

def dump_trips(data, filename):
    # TODO: allow filtering the data by timeframe, origins

    # data is organized by vehicle (with VIN as the key).
    # for now just dump all trips

    trips = []
    for vin in data:
        trips.extend(data[vin]['trips'])

    trips = format_for_json(trips)

    f = open(filename, 'w')
    print >> f, json.dumps(trips)
    f.close()

def dump_vehicle(data, vin, filename = False):
    #  dump of trace results by vehicle's VIN

    trips = data[vin]['trips']

    trips = format_for_json(trips)

    if not filename:
        filename = vin + '_trips.json'

    f = open(vin + '_trips.json', 'w')
    print >> f, json.dumps(trips)
    f.close()

