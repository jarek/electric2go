#!/usr/bin/env python2
# coding=utf-8

from __future__ import unicode_literals
from __future__ import print_function
import time

from jinja2 import Environment, PackageLoader

import cars
import web_helper


MAPS_URL = 'https://maps.google.ca/maps?q={q}&ll={ll}&z=16&t=h'.replace('&', '&amp;')
MAPS_IMAGE_CODE = '<img src="http://maps.googleapis.com/maps/api/staticmap?size=300x250&zoom=15&markers=size:small|{ll}&markers=size:tiny|{other_ll}&center={ll}&visual_refresh=true&sensor=false" alt="map of {q}" width="300" height="250" />'.replace('&', '&amp;')
MAPS_MULTI_CODE = '<img src="http://maps.googleapis.com/maps/api/staticmap?size=300x250&markers=size:small|{ll}&visual_refresh=true&sensor=false" alt="{alt}" width="300" height="250" id="multimap" />'.replace('&', '&amp;')

# For zoom=15 and size 300x250, the map is less than 0.02 degrees across
# in both directions. In practice the observed value varies from 
# roughly 0.007385 degrees latitude to roughly 0.013326 degrees longitude
# (both in Vancouver), with numbers in other cities both north and south
# of Vancouver's latitude (Austin, Berlin) being fairly close.
# If we change displayed map size, we might also need to update this value,
# or come up with a formula to estimate it based on map size and zoom level.
MAP_SIZE_IN_DEGREES = 0.02

timer = []


def import_file(filename):
    with open(filename, 'r') as f:
        result = f.read()

    return result

    # I used to have code here that "minified" CSS by stripping out whitespace,
    # but the size difference is on the order of 3 kB and not worth the effort.
    # (Not to mention the JS is larger and harder to minify.)


def format_latlng(car):
    return '%s,%s' % (car['lat'], car['lng'])


def get_car_info(car, all_cars, city, parse):
    # Extract information specific for web display

    coords = format_latlng(car)
    address = web_helper.format_address(car['address'], city)

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
    other_str = '|'.join(other_ll)

    mapimg = MAPS_IMAGE_CODE.format(ll=coords, other_ll=other_str, q=address)

    title = car['address']
    if title == '':
        # communauto doesn't have the address geocoded. use license plate
        title = car['license_plate']

    return {
        'title': title,
        'coords': coords,
        'vin': car['vin'],
        'license_plate': car['license_plate'],
        'charge': car['fuel'],
        'range': parse.get_range(car),
        'cleanliness_interior': car.get('cleanliness_interior', None),
        'cleanliness_exterior': car.get('cleanliness_exterior', None),
        'map_url': MAPS_URL.format(ll=coords, q=address.replace(' ', '%20')),
        'map_img': mapimg
    }


def format_all_cars_map(all_car_infos):
    if len(all_car_infos) < 2:
        # Don't show map if there's no cars.
        # Also don't show map is there's just one car - the map shown
        # with the rest of car info will be above fold or quite high.
        return ''

    coords = [car['coords'] for car in all_car_infos]
    lls = '|'.join(coords)
    code = MAPS_MULTI_CODE.format(ll=lls, alt='map of all available cars')

    return code


def pluralize(count, string, end_ptr=None, rep_ptr=''):
    if int(count) == 1:
        label = string
    elif end_ptr and string.endswith(end_ptr):
        label = string[:-1*len(end_ptr)] + rep_ptr
    else:
        label = string + 's'

    return '{count:.0f} {label}'.format(count=count, label=label)


def get_timer_info(t=timer):
    return ['<!--%s: %f-->' % (timepoint[0], timepoint[1]) for timepoint in t]


def print_timer_info(t=timer):
    for line in get_timer_info(t):
        print(line)


def print_all_html():
    print('Content-type: text/html\n')

    ttime1 = time.time()

    env = Environment(loader=PackageLoader('frontend', '.'))
    env.filters['count'] = pluralize

    requested_city = web_helper.get_system_and_city()
    electric_cars, cache = web_helper.get_electric_cars(requested_city)

    # get list of cities
    all_cities = [city for system in web_helper.ALL_SYSTEMS
                  for city in cars.get_all_cities(system).values()
                  if city['electric'] == 'some']

    # get car details
    parse = cars.get_carshare_system_module(requested_city['system'], 'parse')
    car_infos = [get_car_info(car, electric_cars, requested_city, parse) for car in electric_cars]

    # supplementary information
    cache_age = (time.time() - cache) if cache else cache
    cache_next_refresh = cars.CACHE_PERIOD - cache_age

    # render big template
    tmpl_layout = env.get_template('layout.html')
    full_html = tmpl_layout.render(displayed_city=requested_city,
                                   cities=all_cities,
                                   all_cars=car_infos,
                                   all_cars_count=len(car_infos),
                                   all_cars_map=format_all_cars_map(car_infos),
                                   cache_age=cache_age,
                                   cache_next_refresh=cache_next_refresh,
                                   block_css=import_file('frontend/style.css'),
                                   block_js=import_file('frontend/sort.js'))

    print(full_html.encode('utf-8'))

    # print timer info separately. TODO: rewrite timers to not be horrible
    ttime2 = time.time()
    timer.append(['total, ms', (ttime2-ttime1)*1000.0])

    print_timer_info(cars.timer)
    print_timer_info()


if __name__ == '__main__':
    print_all_html()
