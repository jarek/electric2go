#!/usr/bin/env python2
# coding=utf-8


def get_cars_from_json(json_data):
    return json_data


def extract_car_basics(car):
    return car['VehicleNo'], car['Latitude'], car['Longitude']


def extract_car_data(car):
    result = {}

    result['timestamp'] = car['RecordedTime']  # TODO: needs to be parsed, is in format like "03:58:21 pm"

    result['vin'] = car['VehicleNo']

    result['lat'] = car['Latitude']
    result['lng'] = car['Longitude']

    result['fuel'] = 0  # not reported in Translink API

    return result
