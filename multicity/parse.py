#!/usr/bin/env python2
# coding=utf-8


def get_cars_from_json(json_data):
    return json_data.get('marker', [])


def extract_car_basics(car):
    return car['hal2option']['id'], car['lat'], car['lng']


def extract_car_data(car):
    result = {}

    vin, lat, lng = extract_car_basics(car)

    result['vin'] = vin
    result['lat'] = lat
    result['lng'] = lng

    result['name'] = car['hal2option']['tooltip']

    return result
