#!/usr/bin/env python3
# coding=utf-8

from __future__ import unicode_literals
from __future__ import print_function
import time

from jinja2 import Environment, PackageLoader

import web_helper
from web_helper import systems


# For zoom=15 and size 300x250, the map is less than 0.02 degrees across
# in both directions. In practice the observed value varies from 
# roughly 0.007385 degrees latitude to roughly 0.013326 degrees longitude
# (both in Vancouver), with numbers in other cities both north and south
# of Vancouver's latitude (Austin, Berlin) being fairly close.
# If we change displayed map size, we might also need to update this value,
# or come up with a formula to estimate it based on map size and zoom level.
MAP_SIZE_IN_DEGREES = 0.02


def google_api_key():
    try:
        with open('google_api_key', 'r') as f:
            key = f.read().strip()
    except:
        key = ''

    return key


def format_latlng(car):
    return '{:f},{:f}'.format(car['lat'], car['lng'])


def get_car_info(car, all_cars, city):
    # Extract information specific for web display

    car = web_helper.fill_in_car(car, city)

    coords = format_latlng(car)

    title = car['address']
    if title == '':
        # communauto doesn't provide the geocoded address. use license plate
        title = car['license_plate']

    # Show other nearby cars on map if they are within the map area.
    # Include only the cars that would actually fit on the map
    # (given zoom level and distance from this car's coords)
    # to avoid unnecessarily long image URLs.
    # We do this by simple subtraction of latitudes/longitudes and comparing
    # against a reference value (declared with comments above).
    # This has some error compared to proper Haversine distance calculation,
    # but at scales involved (~1 km) this shouldn't really matter, especially
    # given the roughly 50-100% margin of error in the reference
    # degree difference value.
    def in_bounds(car1, car2):
        lat_dist = abs(car1['lat'] - car2['lat'])
        lng_dist = abs(car1['lng'] - car2['lng'])
        return lat_dist < MAP_SIZE_IN_DEGREES and lng_dist < MAP_SIZE_IN_DEGREES

    other_ll = [format_latlng(other_car) for other_car in all_cars
                if (other_car['lat'] != car['lat'] and other_car['lng'] != car['lng'])
                and in_bounds(car, other_car)]

    # provide a value that will have either address or coords.
    # some systems don't provide geocoded address.
    address_for_map = car['address'] if car['address'] != '' else coords

    return {
        'title': title,
        'license_plate': car['license_plate'],
        'charge': car['fuel'],
        'range': car['range'],
        'model': car['model'],
        'coords': coords,
        'vin': car['vin'],
        'address_or_coords': address_for_map,
        'other_cars_ll': other_ll,
        'cleanliness_interior': car.get('cleanliness_interior', ''),
        'cleanliness_exterior': car.get('cleanliness_exterior', '')
    }


def pluralize(count, string, end_ptr=None, rep_ptr=''):
    if int(count) == 1:
        label = string
    elif end_ptr and string.endswith(end_ptr):
        label = string[:-1*len(end_ptr)] + rep_ptr
    else:
        label = string + 's'

    return '{count:.0f} {label}'.format(count=count, label=label)


def print_all_html():
    print('Content-type: text/html\n')

    env = Environment(loader=PackageLoader('frontend', '.'), trim_blocks=True, lstrip_blocks=True)
    env.filters['count'] = pluralize

    requested_city = web_helper.get_system_and_city(allow_any_city=False)
    electric_cars, cache = web_helper.get_electric_cars(requested_city)

    # get list of cities
    all_cities = (city for system in web_helper.ALL_SYSTEMS
                  for city in systems.get_all_cities(system).values()
                  if city['electric'] == 'some')
    all_cities = sorted(all_cities, key=lambda c: c['name'])

    # get car details
    car_infos = [get_car_info(car, electric_cars, requested_city) for car in electric_cars]

    car_models = set(car['model'] for car in car_infos)

    # supplementary information
    cache_age = (time.time() - cache) if cache else cache
    cache_next_refresh = web_helper.CACHE_PERIOD - cache_age

    # render big template
    tmpl_layout = env.get_template('layout.html')
    full_html = tmpl_layout.render(displayed_city=requested_city,
                                   cities=all_cities,
                                   all_cars=car_infos,
                                   all_car_models=car_models,
                                   cache_age=cache_age,
                                   cache_next_refresh=cache_next_refresh,
                                   google_api_key=google_api_key())

    try:
        # this works straight-up on Python 3
        print(full_html)
    except UnicodeEncodeError:
        # Python 2 needs an explicit encode in some cases,
        # particularly when using BaseHTTPServer module
        print(full_html.encode('utf-8'))


if __name__ == '__main__':
    print_all_html()
