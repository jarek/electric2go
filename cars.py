#!/usr/bin/env python2
# coding=utf-8

import os
import importlib
import math
import requests
import json
import time
import city_helper


CACHE_PERIOD = 60  # cache data for this many seconds at most
DATA_COLLECTION_INTERVAL_MINUTES = 1  # used in download.py, process.py

root_dir = os.path.dirname(os.path.realpath(__file__))

timer = []


def get_URL(url, extra_headers=None, session=None):
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


def get_file_name(city_data, t):
    filename_format = '%s_%04d-%02d-%02d--%02d-%02d'
    return filename_format % (city_data['name'], t.year, t.month, t.day, t.hour, t.minute)


def get_file_path(city_data, t):
    filename = get_file_name(city_data, t)
    return os.path.join(get_data_dir(city_data['system']), filename)


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
            with open(cached_data_filename, 'r') as f:
                json_text = f.read()

    if not json_text:
        json_text, session = get_URL(city_obj['API_AVAILABLE_VEHICLES_URL'],
                                     city_obj['API_AVAILABLE_VEHICLES_HEADERS'],
                                     session=session)

    # handle JSONP if necessary
    if 'JSONP_CALLBACK_NAME' in city_obj:
        prefix = '{callback}('.format(callback=city_obj['JSONP_CALLBACK_NAME'])
        suffix1 = ');'
        suffix2 = ')'

        if json_text.startswith(prefix):
            if json_text.endswith(suffix1):
                json_text = json_text[len(prefix):-len(suffix1)]
            elif json_text.endswith(suffix2):
                json_text = json_text[len(prefix):-len(suffix2)]

    return json_text, cache, session


def get_electric_cars(city):
    json_text, cache, _ = get_all_cars_text(city)

    time1 = time.time()

    cars = json.loads(json_text).get('placemarks')

    time2 = time.time()
    timer.append(['json size, kB', len(json_text)/1000.0])
    timer.append(['json load, ms', (time2-time1)*1000.0])

    electric_cars = []

    time1 = time.time()

    for car in cars:
        if car['engineType'] == 'ED':
            electric_cars.append(car)

    time2 = time.time()
    timer.append(['list search, ms', (time2-time1)*1000.0])

    return electric_cars, cache


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
    # adapted from http://www.movable-type.co.uk/scripts/latlong.html
    # see also http://stackoverflow.com/questions/27928/how-do-i-calculate-distance-between-two-latitude-longitude-points

    # the js equivalent of this code is used in sort.js
    # - any changes should be reflected in both

    def deg2rad(deg):
        return deg * (math.pi/180.0)

    R = 6371  # Radius of the earth in km
    dLat = deg2rad(ll2[0]-ll1[0])
    dLon = deg2rad(ll2[1]-ll1[1])

    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(deg2rad(ll1[0])) * math.cos(deg2rad(ll2[0])) * \
        math.sin(dLon/2) * math.sin(dLon/2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c  # distance in km
    return d

