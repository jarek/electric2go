#!/usr/bin/env python
# coding=utf-8

import os
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

	address_parts = address.split(',')

	street_parts = address_parts[0].split()

	if street_parts[-1].isdigit() and not street_parts[0].isdigit():
		street_parts.insert(0, street_parts.pop())
		address_parts[0] = ' '.join(street_parts)

	return ','.join(address_parts)

def format_latlng(ll):
	return str(ll[1]) + ',' + str(ll[0])

def format_car(car, city):
	for key in car:
		if isinstance(car[key], basestring):
			car[key] = car[key].encode('ascii','xmlcharrefreplace')

	coords = format_latlng(car['coordinates'])

	info = '<section class="sort" data-loc="' + coords + '">'
	info += '<h3>' + format_address(car['address'], city) + '</h3><p>'

	charge = car['fuel']
	if charge < 20:
		info += '<span style="color: red">Not driveable</span>, '
	else:
		# full charge range is approx 135 km, round down a bit
		# must end trip with more than 20% unless at charging station
		range = 1.2 * (charge-20)
		info += 'Approx range: ' + str(range) + ' km, '

	info += 'charge: ' + str(charge) + '%'

	if car['charging']:
		info += ', charging<br/>'
	else:
		info += '<br/>'

	info += 'Plate: ' + car['name'] + ', '
	info += 'interior: ' + car['interior'].lower() + ', '
	info += 'exterior: ' + car['exterior'].lower() + '<br/>\n'

	mapurl = cars.MAPS_URL.replace('{ll}', coords).replace('{q}', car['address'].replace(' ','%20'))
	info += 'Location: <a href="' + mapurl + '">' + coords + '</a>'
	info += '<span class="distance" data-template=", approx distance: {dist} km"></span><br/>\n'

	info += '<a href="' + mapurl + '">'
	info += cars.MAPS_IMAGE_CODE.replace('{ll}', coords).replace('{q}', car['address'])
	info += '</a>'
	info += '</section>'

	return info

def format_all_cars_map(city):
	all_cars,cache = cars.get_electric_cars(city)

	if len(all_cars) == 0:
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
				formatted_cities.append('<strong>' + data['display'] + '</strong>')
			else:
				formatted_cities.append('<a href="?city=' + city + '">' + data['display'] + '</a>')

	return 'car2go cities with a few electric vehicles: ' + ', '.join(formatted_cities)

def print_timer_info(t = timer):
	for timepoint in t:
		print '<!--%s: %f-->' % (timepoint[0], timepoint[1])

def print_all_html():
	print 'Content-type: text/html\n'

	ttime1 = time.time()

	requested_city = cars.get_city()

	print '<!doctype html>'
	print '<meta charset="utf-8" />'
	print '<title>electric car2go vehicles in ' + cars.CITIES[requested_city]['display'] + '</title>'
	print '<style type="text/css" media="screen,projection">'
	print import_file('style.css') + '</style>'

	print '<nav>' + get_formatted_all_cities(requested_city) + '</nav>'

	electric_cars,cache = get_formatted_electric_cars(requested_city)

	count = len(electric_cars)
	plural = 's' if count != 1 else ''

	print '<h2>' + str(count) + ' electric car' + plural,
	print 'currently available in ' + cars.CITIES[requested_city]['display'] + '</h2>'

	print format_all_cars_map(requested_city)

	for car in electric_cars:
		print car

	ttime2 = time.time()
	timer.append(['total, ms', (ttime2-ttime1)*1000.0])

	print '<footer>',
	if cache:
		print 'Using cached data. Data age: %i seconds, next refresh in %i seconds.' % (cache, cars.CACHE_PERIOD - cache)
	print 'This product uses the car2go API but is not endorsed or certified by car2go.</footer>'
	
	print '<script type="text/javascript">'
	print import_file('sort.js') + '</script>'

	print_timer_info(cars.timer)
	print_timer_info()


if __name__ == '__main__':
	print_all_html()
