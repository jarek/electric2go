# coding=utf-8

import os
import importlib
from datetime import datetime
from math import radians, sin, cos, asin, sqrt


root_dir = os.path.dirname(os.path.realpath(__file__))


def get_data_dir(system):
    return os.path.join(root_dir, 'data', system)


def get_current_file_path(city_data):
    data_dir = get_data_dir(city_data['system'])
    return os.path.join(data_dir, 'current_%s' % city_data['name'])


def get_file_name(city_name, t):
    filename_format = '%s_%04d-%02d-%02d--%02d-%02d'
    return filename_format % (city_name, t.year, t.month, t.day, t.hour, t.minute)


def get_file_path(city_data, t):
    filename = get_file_name(city_data['name'], t)
    return os.path.join(get_data_dir(city_data['system']), filename)


def output_file_name(description, extension=''):
    file_name = '{date}_{desc}'.format(
        date=datetime.now().strftime('%Y%m%d-%H%M%S'),
        desc=description)

    if extension:
        file_name = '{name}.{ext}'.format(name=file_name, ext=extension)

    return file_name


def fill_in_city_information(system, city_name, city_data):
    city_data['system'] = system
    city_data['name'] = city_name

    if 'display' not in city_data:
        city_data['display'] = city_name.title()

    if 'MAP_SIZES' not in city_data and 'MAP_LIMITS' in city_data:
        # default to 1920x1080 if we have other map data
        city_data['MAP_SIZES'] = {'MAP_X': 1920, 'MAP_Y': 1080}

    # set some default values if not present
    city_data.setdefault('electric', False)
    city_data.setdefault('of_interest', False)
    city_data.setdefault('number_first_address', False)
    city_data.setdefault('API_AVAILABLE_VEHICLES_HEADERS', None)
    city_data.setdefault('API_KNOCK_HEAD_URL', None)

    # provide the range estimator
    city_data['range_estimator'] = getattr(get_parser(system), 'get_range', None)

    return city_data


def _get_carshare_system_module(system_name, module_name=''):
    if module_name == '':
        lib_name = system_name
    else:
        lib_name = '%s.%s' % (system_name, module_name)

    return importlib.import_module(lib_name)


def _get_all_cities_raw(system):
    city_module = _get_carshare_system_module(system, 'city')

    return getattr(city_module, 'CITIES')


def get_all_cities(system):
    all_cities = _get_all_cities_raw(system)

    return {city_name: fill_in_city_information(system, city_name, all_cities[city_name])
            for city_name in all_cities}


def get_city_by_name(system, city_name):
    all_cities = _get_all_cities_raw(system)
    city_data = all_cities[city_name]
    return fill_in_city_information(system, city_name, city_data)


_parse_modules = {}
def get_parser(system):
    # Function with a mini-cache since getting parser requires importing
    # modules which might be pretty slow, and parsers might get requested a lot
    # Python 3 has a @functools.lru_cache but Python 2 doesn't :(
    # so hack our own simple one.
    if system not in _parse_modules:
        _parse_modules[system] = _get_carshare_system_module(system, 'parse')

    return _parse_modules[system]


def dist(ll1, ll2):
    # Haversine formula implementation to get distance between two points
    # adapted from http://www.movable-type.co.uk/scripts/latlong.html
    # see also http://stackoverflow.com/questions/27928/calculate-distance-between-two-ll-points
    # and http://stackoverflow.com/questions/4913349/haversine-formula-in-python

    # the js equivalent of this code is used in sort.js
    # - any changes should be reflected in both

    earth_radius = 6371  # Radius of the earth in km

    lat1, lng1 = ll1
    lat2, lng2 = ll2

    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)

    # Using d_lat = lat2_rad - lat1_rad gives marginally different results,
    # because floating point
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)

    a = sin(d_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(d_lng/2)**2
    c = 2 * asin(sqrt(a))

    return earth_radius * c
