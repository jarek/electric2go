#!/usr/bin/env python
# coding=utf-8

import cgi
import math
import simplejson as json
import time
import cars

timer = []

def get_param(param_name):
    arguments = cgi.FieldStorage()

    if param_name in arguments:
        return arguments[param_name].value
    else:
        return False

def fill_in_info(car, query_ll = False):
    # estimate range
    # full charge range is approx 135 km, round down a bit
    # must end trip with more than 20% unless at charging station
    if car['engineType'] == 'ED':
        if car['fuel'] > 20:
            car['range'] = int(math.floor(1.2 * (car['fuel']-20)))
        else:
            car['range'] = 0

    coords = (car['coordinates'][1], car['coordinates'][0])

    if query_ll:
        car['distance'] = cars.dist(coords, query_ll)

    return car

def json_respond():
    print 'Content-type: application/json\n'

    ttime1 = time.time()

    requested_city = cars.get_city()
    electric_cars,cache = cars.get_electric_cars(requested_city)

    limit = get_param('limit')
    if limit:
        limit = int(limit)
    else:
        limit = 5

    query_ll = get_param('ll')
    if query_ll:
        query_ll = query_ll.split(',')
        query_ll[0] = float(query_ll[0])
        query_ll[1] = float(query_ll[1])

    results = []
    for car in electric_cars:
        results.append(fill_in_info(car, query_ll))

    if query_ll:
        results.sort(key = lambda x: x['distance'])

    results = results[:limit]

    result = {'placemarks': results}

    if cache:
        result['cache'] = True
        result['cache_age'] = cache
    else:
        result['cache'] = False

    timer.append(['total, ms', (time.time()-ttime1)*1000.0])

    if get_param('debug'):
        cars.timer.extend(timer)
        result['timer'] = cars.timer

    print json.dumps(result)


if __name__ == '__main__':
    json_respond()

