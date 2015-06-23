#!/usr/bin/env python2
# coding=utf-8

from __future__ import print_function
import json
import time
import cars
import web_helper

timer = []


def get_info(car, query_ll=False):
    parse = cars.get_carshare_system_module(web_helper.WEB_SYSTEM, 'parse')

    car['range'] = parse.get_range(car)

    if query_ll:
        car['distance'] = cars.dist((car['lat'], car['lng']), query_ll)

    return car


def json_respond():
    print('Content-type: application/json\n')

    ttime1 = time.time()

    requested_city = web_helper.get_city()
    electric_cars, cache = web_helper.get_electric_cars(requested_city)

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

    results = [get_info(car, query_ll) for car in electric_cars]

    if query_ll:
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

    print(json.dumps(result))


if __name__ == '__main__':
    json_respond()

