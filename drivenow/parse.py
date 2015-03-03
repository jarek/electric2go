#!/usr/bin/env python2
# coding=utf-8


def get_cars_from_json(json_data):
    if 'cars' in json_data and 'items' in json_data['cars']:
        return json_data['cars']['items']
    else:
        return []


def extract_car_basics(car):
    return car['id'], car['latitude'], car['longitude']


def extract_car_data(car):
    result = {}

    result['vin'] = car['id']
    result['name'] = car['name']
    result['license_plate'] = car['licensePlate']

    result['model'] = car['modelName']
    result['color'] = car['color']

    result['lat'] = car['latitude']
    result['lng'] = car['longitude']

    result['address'] = ','.join(car['address'])

    result['fuel'] = car['fuelLevel'] * 100
    result['fuel_type'] = car['fuelType']

    result['transmission'] = car['transmission']

    result['cleanliness_interior'] = car['innerCleanliness']

    return result
