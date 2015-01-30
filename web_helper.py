#!/usr/bin/env python2
# coding=utf-8

import sys
import cgi
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

    return {'name': city_name,
            'data': all_cities[city_name]}
