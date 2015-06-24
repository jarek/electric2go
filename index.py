#!/usr/bin/env python2
# coding=utf-8

from __future__ import print_function
import time

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


def format_car(car, city, all_cars=False):
    """
    :type all_cars: list
    """

    coords = format_latlng(car)
    address = web_helper.format_address(car['address'], city)

    info = '<section class="sort" data-loc="%s">' % coords
    info += '<h3>%s</h3>' % address
    info += '<p><!--vin: %s-->' % car['vin']

    charge = car['fuel']
    parse = cars.get_carshare_system_module(city['system'], 'parse')
    car_range = parse.get_range(car)
    if car_range == 0:
        info += '<span style="color: red">Not driveable</span>, '
    else:
        info += 'Approx range: %s km, ' % car_range

    info += 'charge: %s%%' % charge

    if car['charging']:
        info += ', charging<br/>'
    else:
        info += '<br/>'

    info += 'Plate: %s' % car['license_plate']
    if 'cleanliness_interior' in car:
        info += ', interior: %s' % car['cleanliness_interior'].lower().replace('_', ' ')
    if 'cleanliness_exterior' in car:
        info += ', exterior: %s' % car['cleanliness_exterior'].lower().replace('_', ' ')
    info += '<br/>\n'

    mapurl = MAPS_URL.format(ll=coords, q=address.replace(' ', '%20'))

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
    other_ll = ''
    if all_cars:
        other_ll = []
        for other_car in all_cars:
            formatted = format_latlng(other_car)
            if formatted != coords:
                # if it's not the same car, compare with current car's coordinates

                lat_dist = abs(other_car['lat'] - car['lat'])
                lng_dist = abs(other_car['lng'] - car['lng'])

                if lat_dist < MAP_SIZE_IN_DEGREES \
                and lng_dist < MAP_SIZE_IN_DEGREES:
                    other_ll.append(formatted)

        other_ll = '|'.join(other_ll)

    mapimg = MAPS_IMAGE_CODE.format(ll=coords, other_ll=other_ll, q=address)

    info += 'Location: <a href="%s">%s</a>' % (mapurl, coords)
    info += '<span class="distance" '
    info += 'data-template=", approx distance: {dist} km{min}"></span><br/>\n'

    info += '<a href="%s">%s</a>' % (mapurl, mapimg)
    info += '</section>'

    return info


def format_all_cars_map(city):
    # TODO: this depends on caching, if there is no caching it makes a duplicate request
    all_cars, cache = web_helper.get_electric_cars(city)

    if len(all_cars) < 2:
        # Don't show map if there's no cars.
        # Also don't show map is there's just one car - the map shown
        # with the rest of car info will be above fold or quite high.
        return ''

    coords = [format_latlng(car) for car in all_cars]
    lls = '|'.join(coords)
    code = MAPS_MULTI_CODE.format(ll=lls, alt='map of all available cars')

    return code


def get_formatted_electric_cars(city):
    electric_cars, cache = web_helper.get_electric_cars(city)

    result = [format_car(car, city, electric_cars) for car in electric_cars]

    return result, cache


def get_formatted_all_cities(requested_city):
    formatted_cities = []

    for system in web_helper.ALL_SYSTEMS:
        all_cities = cars.get_all_cities(system)
        for city_key, data in sorted(all_cities.items()):
            # show only cities that have some electric cars,
            # but not a full fleet of electric.
            # there's nothing to show for cities that don't have any,
            # and there's no benefit over official apps for all-fleet.
            if data['electric'] == 'some':
                if system == requested_city['system'] and city_key == requested_city['name']:
                    formatted_cities.append(
                        '<strong>%s (%s)</strong>' % (data['display'], system))
                else:
                    formatted_cities.append(
                        '<a href="?system=%s&city=%s">%s (%s)</a>' % (system, city_key, data['display'], system))

    return 'cities with a few electric vehicles: %s' % \
        ', '.join(formatted_cities)


def pluralize(amount, text):
    plural = 's' if amount != 1 else ''
    return '%d %s%s' % (amount, text, plural)


def get_timer_info(t=timer):
    return ['<!--%s: %f-->' % (timepoint[0], timepoint[1]) for timepoint in t]


def print_timer_info(t=timer):
    for line in get_timer_info(t):
        print(line)


def print_all_html():
    print('Content-type: text/html\n')

    ttime1 = time.time()

    requested_city = web_helper.get_system_and_city()

    print('<!doctype html>')
    print('<meta charset="utf-8" />')
    print('<title>electric carshare vehicles in %s</title>' %
          requested_city['display'])
    print('''<!-- Hello! If you're interested, the source code for this page is
        available at https://github.com/jarek/electric2go -->''')
    print('<style type="text/css" media="screen,projection">')
    print(import_file('frontend/style.css'))
    print('</style>')

    print('<nav>%s</nav>' % get_formatted_all_cities(requested_city))

    electric_cars, cache = get_formatted_electric_cars(requested_city)

    print('<h2>%s currently available in %s</h2>' %
          (pluralize(len(electric_cars), 'electric car'),
           requested_city['display']))

    print(format_all_cars_map(requested_city))

    for car in electric_cars:
        print(car)

    ttime2 = time.time()
    timer.append(['total, ms', (ttime2-ttime1)*1000.0])

    print('<footer>', end='')
    if cache:
        cache_age = time.time() - cache
        print('Using cached data. Data age: %s, next refresh in %s.' %
              (pluralize(cache_age, 'second'),
               pluralize(cars.CACHE_PERIOD - cache_age, 'second')))
    if requested_city['system'] == 'car2go':
        print('''This product uses the car2go API but is not endorsed
              or certified by car2go.</footer>''')
    
    print('<script type="text/javascript">')
    print(import_file('frontend/sort.js'))
    print('</script>')

    print_timer_info(cars.timer)
    print_timer_info()


if __name__ == '__main__':
    print_all_html()
