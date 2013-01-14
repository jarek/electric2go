#!/usr/bin/env python
# coding=utf-8

import time
import cars

timer = []

def format_car(car):
	for key in car:
		if isinstance(car[key], basestring):
			car[key] = car[key].encode('ascii','xmlcharrefreplace')

	info = 'Location: ' + car['address'] + '<br/>'

	charge = car['fuel']
	if charge < 20:
		info += '<span color="red">Not driveable</span>, '
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

	info += 'Plate: ' + car['name'] + '<br/>'
	info += 'Interior: ' + car['interior'] + \
		', exterior: ' + car['exterior'] + '<br/>'

	coords = str(car['coordinates'][1]) + ',' + str(car['coordinates'][0])
	mapurl = cars.MAPS_URL.replace('{ll}', coords).replace('{q}', car['address'].replace(' ','%20'))
	info += 'Coords: <a href="' + mapurl + '">' + coords + '<br/>'

	info += cars.MAPS_IMAGE_CODE.replace('{ll}', coords).replace('{q}', car['address'])
	info += '</a>'

	return info

def get_formatted_electric_cars(city):
	electric_cars = cars.get_electric_cars(city)
	result = []

	for car in electric_cars:
		result.append(format_car(car))

	return result

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

	return '<p>car2go cities with a few electric vehicles: ' + ', '.join(formatted_cities)

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

	print get_formatted_all_cities(requested_city)

	electric_cars = get_formatted_electric_cars(requested_city)

	count = len(electric_cars)
	plural = 's' if count != 1 else ''

	print '<p>' + str(count) + ' electric car' + plural,
	print 'currently available in ' + cars.CITIES[requested_city]['display']

	for car in electric_cars:
		print '<p>' + car

	ttime2 = time.time()
	timer.append(['total, ms', (ttime2-ttime1)*1000.0])

	print_timer_info(cars.timer)
	print_timer_info()


if __name__ == '__main__':
	print_all_html()
