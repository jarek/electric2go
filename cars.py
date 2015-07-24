#!/usr/bin/env python2
# coding=utf-8

import os
import importlib
import time
from datetime import datetime
from math import radians, sin, cos, atan2, sqrt

import requests

import city_helper


CACHE_PERIOD = 60  # cache data for this many seconds at most
DATA_COLLECTION_INTERVAL_MINUTES = 1  # used in download.py, process.py

root_dir = os.path.dirname(os.path.realpath(__file__))

timer = []


def get_url(url, extra_headers=None, session=None):
    htime1 = time.time()

    if session is None:
        session = requests.Session()

    r = session.get(url, headers=extra_headers)

    htime2 = time.time()
    timer.append(['http get, ms', (htime2-htime1)*1000.0])

    return r.content, session


def get_data_dir(system):
    return os.path.join(root_dir, 'data', system)


def get_current_filename(city_data):
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


def get_all_cars_text(city_obj, force_download=False, session=None):
    json_text = None
    cache = False

    cached_data_filename = get_current_filename(city_obj)
    if os.path.exists(cached_data_filename) and not force_download:
        cached_data_timestamp = os.path.getmtime(cached_data_filename)
        cached_data_age = time.time() - cached_data_timestamp
        if cached_data_age < CACHE_PERIOD:
            cache = cached_data_timestamp
            timer.append(['using cached data, age in seconds', cached_data_age])
            with open(cached_data_filename, 'rb') as f:
                json_text = f.read()

    if not json_text:
        json_text, session = get_url(city_obj['API_AVAILABLE_VEHICLES_URL'],
                                     city_obj['API_AVAILABLE_VEHICLES_HEADERS'],
                                     session=session)

    # handle JSONP if necessary
    if 'JSONP_CALLBACK_NAME' in city_obj:
        prefix = '{callback}('.format(callback=city_obj['JSONP_CALLBACK_NAME'])
        suffix1 = ');'
        suffix2 = ')'

        json_text = json_text.decode('utf-8')

        if json_text.startswith(prefix):
            if json_text.endswith(suffix1):
                json_text = json_text[len(prefix):-len(suffix1)]
            elif json_text.endswith(suffix2):
                json_text = json_text[len(prefix):-len(suffix2)]

        json_text = json_text.encode('utf-8')

    return json_text, cache, session


def get_all_cities(system):
    city_module = get_carshare_system_module(system, 'city')

    all_cities = getattr(city_module, 'CITIES')

    all_cities = city_helper.fill_in_information(system, all_cities)

    return all_cities


def get_carshare_system_module(system_name, module_name=''):
    if module_name == '':
        lib_name = system_name
    else:
        lib_name = '%s.%s' % (system_name, module_name)

    return importlib.import_module(lib_name)


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
    # I think in theory the shorter calculation c = 2 * asin(sqrt(a))
    # is mathematically the same. In practice, floating point precision errors
    # break my tests on the 14th decimal digit.
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return earth_radius * c
