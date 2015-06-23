#!/usr/bin/env python2
# coding=utf-8

import sys
import cgi
import json
import time
import cars


# at least for now, web pages use only 'car2go' system
WEB_SYSTEM = 'car2go'


def get_param(param_name):
    arguments = cgi.FieldStorage()

    if param_name in arguments:
        return arguments[param_name].value
    else:
        return False


def get_city():
    city_name = 'vancouver'  # default to Vancouver

    all_cities = cars.get_all_cities(WEB_SYSTEM)

    param = get_param('city') or (sys.argv[1].lower() if len(sys.argv) > 1 else False)

    if param in all_cities:
        city_name = param

    return all_cities[city_name]


def get_electric_cars(city):
    json_text, cache, _ = cars.get_all_cars_text(city)

    time1 = time.time()

    parse = cars.get_carshare_system_module(WEB_SYSTEM, 'parse')

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
