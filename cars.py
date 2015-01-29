#!/usr/bin/env python2
# coding=utf-8

import cgi
import os
import sys
import math
import urllib2
import simplejson as json
import time


CACHE_PERIOD = 60 # cache data for this many seconds at most
DATA_COLLECTION_INTERVAL_MINUTES = 1 # used in download.py, process.py

root_dir = os.path.dirname(os.path.realpath(__file__))
filename_format = '%s_%04d-%02d-%02d--%02d-%02d'

timer = []


def get_URL(url):
    # TODO: consider handling if-none-match, or modified-since, or etag, 
    # or something similar
    # http://www.diveintopython.net/http_web_services/etags.html
    # Maybe before doing so, look into existing data and see 
    # how often the data doesn't change over a minute or over five minutes.
    # At first glance it doesn't look like the the car2go server is sending
    # either last-modified or etag, actually.

    # TODO: also support gzip, if urllib doesn't for me. Connection 
    # establishment is likely to be much of the delay, but perhaps not all.

    # TODO: Maybe try to support keep-alive too? Not sure if I can do it 
    # over separate script runs...

    htime1 = time.time()

    html = urllib2.urlopen(url).read()

    htime2 = time.time()
    timer.append(['http get, ms', (htime2-htime1)*1000.0])

    return html

def get_data_dir(system):
    return os.path.join(root_dir, 'data', system)

def get_current_filename(city_data):
    data_dir = get_data_dir(city_data['system'])
    return os.path.join(data_dir, 'current_%s' % city_data['name'])

def get_all_cars_text(city_obj, force_download=False):
    json_text = None
    cache = False

    cached_data_filename = get_current_filename(city_obj['data'])
    if os.path.exists(cached_data_filename) and not force_download:
        cached_data_timestamp = os.path.getmtime(cached_data_filename)
        cached_data_age = time.time() - cached_data_timestamp
        if cached_data_age < CACHE_PERIOD:
            cache = cached_data_timestamp
            timer.append(['using cached data, age in seconds', cached_data_age])
            with open(cached_data_filename, 'r') as f:
                json_text = f.read()

    if not json_text:
        json_text = get_URL(city_obj['data']['API_URL_AVAILABLE_VEHICLES'])

    return json_text, cache

def get_electric_cars(city):
    json_text,cache = get_all_cars_text(city)

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

    return electric_cars,cache

def get_city():
    city_name = 'vancouver' # default to Vancouver

    # look for http param first
    # if http param not present, look for command line param
    
    param = None
    arguments = cgi.FieldStorage()

    if 'city' in arguments:
        param = str(arguments['city'].value).lower()
    elif len(sys.argv) > 1:
        param = sys.argv[1].lower()

    all_cities = get_all_cities()
    if param in all_cities:
        city_name = param

    return {'name': city_name,
            'data': all_cities[city_name]}

def get_all_cities(system="car2go"):
    # TODO: migrate invocations of this function from depening on the default param,
    # specify explicitly instead

    if system == "car2go":
        from car2go import city
        all_cities = city.CITIES
    else:
        raise KeyError("Unknown system:" % system)

    for city_key in all_cities:
        all_cities[city_key]['system'] = system
        all_cities[city_key]['name'] = city_key

    return all_cities

def dist(ll1, ll2):
    # adapted from http://www.movable-type.co.uk/scripts/latlong.html
    # see also http://stackoverflow.com/questions/27928/how-do-i-calculate-distance-between-two-latitude-longitude-points

    # the js equivalent of this code is used in sort.js
    # - any changes should be reflected in both

    def deg2rad(deg):
        return deg * (math.pi/180.0)

    R = 6371 # Radius of the earth in km
    dLat = deg2rad(ll2[0]-ll1[0])
    dLon = deg2rad(ll2[1]-ll1[1])

    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(deg2rad(ll1[0])) * math.cos(deg2rad(ll2[0])) * \
        math.sin(dLon/2) * math.sin(dLon/2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c # distance in km
    return d

