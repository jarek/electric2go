# coding=utf-8

import os
import sys
import cgi
import json

# ask script to look for the electric2go package in one directory up
# you might want to hardcode a path instead
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from electric2go import dist, download, systems  # dist used in api.py


# systems are loaded dynamically based on their name,
# so the easiest thing is to manually define a list
# of systems with mixed fleets to search
ALL_SYSTEMS = ['car2go', 'drivenow', 'communauto']

DEFAULT_SYSTEM = 'drivenow'
DEFAULT_CITY = 'london'

CACHE_PERIOD = 60  # cache data for this many seconds at most

request_timer = []


def get_param(param_name):
    arguments = cgi.FieldStorage()

    if param_name in arguments:
        return arguments[param_name].value
    else:
        return False


def get_arg(param_number):
    return sys.argv[param_number].lower() if len(sys.argv) > param_number else False


def get_system_and_city(allow_any_city=True):
    system = get_param('system') or get_arg(1)
    city = get_param('city') or get_arg(2)

    if system in ALL_SYSTEMS:
        try:
            city_data = systems.get_city_by_name(system, city)
            if allow_any_city or city_data['electric'] == 'some':
                return city_data
        except KeyError:
            # city name not valid, fall through to default
            pass

    # if city or system were incorrect, return default
    return systems.get_city_by_name(DEFAULT_SYSTEM, DEFAULT_CITY)


def get_electric_cars(city):
    api_text, cache = download.get_current(city, CACHE_PERIOD)

    parse = systems.get_parser(city['system'])
    all_cars = parse.get_cars_from_json(json.loads(api_text.decode('utf-8')))
    parsed_cars = [parse.extract_car_data(car) for car in all_cars]

    electric_cars = [car for car in parsed_cars if car['electric']]

    return electric_cars, cache


def fill_in_car(car, city):
    car['range'] = city['range_estimator'](car)
    car['address'] = format_address(car['address'], city)

    return car


def format_address(address, city):
    if city['system'] == 'drivenow' and city['name'] == 'london':
        # London has an annoying scheme that includes "London" in
        # all geolocated address which is pretty useless
        # as all cars are in London.
        address = address.replace(' London', '')

    if not city['number_first_address']:
        return address

    # If possible and appropriate, try to reformat street address
    # to more usual form used in English-speaking areas.
    # Except for designated parking areas, API always returns
    # German-style "Main St 100", change it to "100 Main St"

    address_parts = address.split(',')

    street_parts = address_parts[0].split()

    if street_parts[-1].isdigit() and not street_parts[0].isdigit():
        street_parts.insert(0, street_parts.pop())
        address_parts[0] = ' '.join(street_parts)

    return ','.join(address_parts)
