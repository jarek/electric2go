#!/usr/bin/env python2
# coding=utf-8

from __future__ import unicode_literals
from __future__ import print_function
import json
import time

import cars
import web_helper

timer = []


def fill_in_distance(car, query_ll):
    car['distance'] = cars.dist((car['lat'], car['lng']), query_ll)
    return car


def json_respond():
    print('Content-type: application/json\n')

    ttime1 = time.time()

    requested_city = web_helper.get_system_and_city()
    electric_cars, cache = web_helper.get_electric_cars(requested_city)

    results = [web_helper.fill_in_car(car, requested_city) for car in electric_cars]

    limit = web_helper.get_param('limit')
    if limit:
        limit = int(limit)
    else:
        limit = 5

    query_ll = web_helper.get_param('ll')
    if query_ll:
        query_ll = query_ll.split(',')
        query_ll[0] = float(query_ll[0])
        query_ll[1] = float(query_ll[1])

        results = [fill_in_distance(car, query_ll) for car in results]
        results.sort(key=lambda x: x['distance'])

    results = results[:limit]

    result = {'cars': results}

    if cache:
        result['cache'] = True
        result['cache_age'] = cache
    else:
        result['cache'] = False

    timer.append(['total, ms', (time.time()-ttime1)*1000.0])

    if web_helper.get_param('debug'):
        cars.timer.extend(timer)
        result['timer'] = cars.timer

    print(json.dumps(result).encode('utf-8'))


if __name__ == '__main__':
    json_respond()
