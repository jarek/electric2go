#!/usr/bin/env python2
# coding=utf-8


def get_cars_from_json(json_data):
    if 'Vehicules' in json_data:
        return json_data['Vehicules']
    else:
        return []


def extract_car_basics(car):
    return car['Id'], car['Position']['Lat'], car['Position']['Lon']


def extract_car_data(car):
    result = {}

    vin, lat, lng = extract_car_basics(car)

    result['vin'] = vin
    result['name'] = car['Name']
    result['license_plate'] = car['Immat']

    result['model'] = car['ModelName']

    result['lat'] = lat
    result['lng'] = lng

    result['fuel'] = car['EnergyLevel']

    return result
