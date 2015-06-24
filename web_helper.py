#!/usr/bin/env python2
# coding=utf-8

import sys
import cgi
import json
import time

import cars


# systems are loaded dynamically based on their name,
# so the easiest thing is to manually define a list
# of systems with mixed fleets to search
ALL_SYSTEMS = ['car2go', 'drivenow', 'communauto']

DEFAULT_SYSTEM = 'drivenow'
DEFAULT_CITY = 'london'


def get_param(param_name):
    arguments = cgi.FieldStorage()

    if param_name in arguments:
        return arguments[param_name].value
    else:
        return False


def get_arg(param_number):
    return sys.argv[param_number].lower() if len(sys.argv) > param_number else False


def get_system_and_city():
    system = get_param('system') or get_arg(1)
    city = get_param('city') or get_arg(2)

    if system in ALL_SYSTEMS:
        all_cities = cars.get_all_cities(system)
        if city in all_cities:
            city_data = all_cities[city]
            city_data.update(system=system)
            return city_data

    # if city or system were incorrect, return default
    all_cities = cars.get_all_cities(DEFAULT_SYSTEM)
    city_data = all_cities[DEFAULT_CITY]
    city_data.update(system=DEFAULT_SYSTEM)
    return city_data


def get_electric_cars(city):
    json_text, cache, _ = cars.get_all_cars_text(city)

    time1 = time.time()

    parse = cars.get_carshare_system_module(city['system'], 'parse')

    all_cars = parse.get_cars_from_json(json.loads(json_text.decode('utf-8')))

    parsed_cars = [parse.extract_car_data(car) for car in all_cars]

    time2 = time.time()
    cars.timer.append(['json size, kB', len(json_text)/1000.0])
    cars.timer.append(['json load, ms', (time2-time1)*1000.0])

    time1 = time.time()

    electric_cars = [car for car in parsed_cars if car['electric']]

    time2 = time.time()
    cars.timer.append(['list search, ms', (time2-time1)*1000.0])

    return electric_cars, cache


def format_address(address, city):
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
