#!/usr/bin/env python
# coding=utf-8

import os
import math
import time
import cars

timer = []

def import_file(filename):
    result = ''

    if os.path.exists(filename):
        f = open(filename, 'r')
        result = f.read().strip()
        f.close()

    if filename.endswith('.css'):
        result = ' '.join(result.split())

    # TODO: not doing the above for js because split() uses all whitespace,
    # including newlines, breaking on js "//" comments.
    # see if removing the comments or something might be worth it.
    # difference in size to transfer with whitespace removed is
    # negligible. with comments removed it's about ~10% on a ~10 car page.
    # not sure if I want to send uncommented js to gain that, really.

    return result

def format_address(address, city):
    if not cars.CITIES[city]['number_first_address']:
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

def format_latlng(ll):
    return '%s,%s' % (ll[1], ll[0])

def format_car(car, city):
    # something in Python doesn't like the Unicode returned by API,
    # so encode all strings explicitly
    for key in car:
        if isinstance(car[key], basestring):
            car[key] = car[key].encode('ascii','xmlcharrefreplace')

    coords = format_latlng(car['coordinates'])
    address = format_address(car['address'], city)

    info = '<section class="sort" data-loc="%s">' % coords
    info += '<h3>%s</h3>' % address
    info += '<p><!--vin: %s-->' % car['vin']

    charge = car['fuel']
    if charge < 20:
        info += '<span style="color: red">Not driveable</span>, '
    else:
        # full charge range is approx 135 km, round down a bit
        # must end trip with more than 20% unless at charging station
        range = int(math.floor(1.2 * (charge-20)))
        info += 'Approx range: %s km, ' % range

    info += 'charge: %s%%' % charge

    if car['charging']:
        info += ', charging<br/>'
    else:
        info += '<br/>'

    info += 'Plate: %s, interior: %s, exterior: %s<br/>\n' % \
        (car['name'], car['interior'].lower(), car['exterior'].lower())

    mapurl = cars.MAPS_URL.replace('{ll}', coords)
    mapurl = mapurl.replace('{q}', address.replace(' ','%20'))

    mapimg = cars.MAPS_IMAGE_CODE.replace('{ll}', coords)
    mapimg = mapimg.replace('{q}', address)

    info += 'Location: <a href="%s">%s</a>' % (mapurl, coords)
    info += '<span class="distance" '
    info += 'data-template=", approx distance: {dist} km"></span><br/>\n'

    info += '<a href="%s">%s</a>' % (mapurl, mapimg)
    info += '</section>'

    return info

def format_all_cars_map(city):
    all_cars,cache = cars.get_electric_cars(city)

    if len(all_cars) < 2:
        # Don't show map if there's no cars.
        # Also don't show map is there's just one car - the map shown
        # with the rest of car info will be above fold or quite high.
        return ''

    coords = list(format_latlng(car['coordinates']) for car in all_cars)

    code = cars.MAPS_MULTI_CODE.replace('{ll}', '|'.join(coords))
    code = code.replace('{alt}', 'map of all available cars')

    return code

def get_formatted_electric_cars(city):
    electric_cars,cache = cars.get_electric_cars(city)
    result = []

    for car in electric_cars:
        result.append(format_car(car, city))

    return result,cache

def get_formatted_all_cities(requested_city):
    formatted_cities = []

    for city,data in sorted(cars.CITIES.iteritems()):
        # show only cities that have some electric cars,
        # but not a full fleet of electric.
        # there's nothing to show for cities that don't have any,
        # and there's no benefit over official apps for all-fleet.
        if data['electric'] == 'some':
            if city == requested_city:
                formatted_cities.append(
                    '<strong>%s</strong>' % data['display'])
            else:
                formatted_cities.append(
                    '<a href="?city=%s">%s</a>' % (city, data['display']))

    return 'car2go cities with a few electric vehicles: %s' % \
        ', '.join(formatted_cities)

def pluralize(amount, text):
    plural = 's' if amount != 1 else ''
    return '%d %s%s' % (amount, text, plural)

def print_timer_info(t = timer):
    for timepoint in t:
        print '<!--%s: %f-->' % (timepoint[0], timepoint[1])

def print_all_html():
    print 'Content-type: text/html\n'

    ttime1 = time.time()

    requested_city = cars.get_city()

    print '<!doctype html>'
    print '<meta charset="utf-8" />'
    print '<title>electric car2go vehicles in %s</title>' % \
        cars.CITIES[requested_city]['display']
    print '''<!-- Hello! If you're interested, the source code for this page is
        available at https://github.com/qviri/electric2go -->'''
    print '<style type="text/css" media="screen,projection">'
    print import_file('style.css')
    print '</style>'

    print '<nav>%s</nav>' % get_formatted_all_cities(requested_city)

    electric_cars,cache = get_formatted_electric_cars(requested_city)

    print '<h2>%s currently available in %s</h2>' % \
        (pluralize(len(electric_cars), 'electric car'), 
        cars.CITIES[requested_city]['display'])

    print format_all_cars_map(requested_city)

    for car in electric_cars:
        print car

    ttime2 = time.time()
    timer.append(['total, ms', (ttime2-ttime1)*1000.0])

    print '<footer>',
    if cache:
        cache_age = time.time() - cache
        print 'Using cached data. Data age: %s, next refresh in %s.' % \
            (pluralize(cache_age, 'second'),
            pluralize(cars.CACHE_PERIOD - cache_age, 'second'))
    print '''This product uses the car2go API 
        but is not endorsed or certified by car2go.</footer>'''
    
    print '<script type="text/javascript">'
    print import_file('sort.js')
    print '</script>'

    print_timer_info(cars.timer)
    print_timer_info()


if __name__ == '__main__':
    print_all_html()

