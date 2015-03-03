#!/usr/bin/env python2
# coding=utf-8


def get_cars_from_json(json_data):
    if 'placemarks' in json_data:
        return json_data['placemarks']
    else:
        return []


def extract_car_basics(car):
    return car['vin'], car['coordinates'][1], car['coordinates'][0]


def extract_car_data(car):
    result = {}

    result['vin'] = car['vin']
    result['license_plate'] = car['name']

    result['model'] = 'smart fortwo'

    result['lat'] = car['coordinates'][1]
    result['lng'] = car['coordinates'][0]

    result['address'] = car['address']

    result['fuel'] = car['fuel']
    result['fuel_type'] = car['engineType']

    result['transmission'] = 'A'

    result['cleanliness_interior'] = car['interior']
    result['cleanliness_exterior'] = car['exterior']

    return result
