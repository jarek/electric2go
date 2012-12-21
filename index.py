#!/usr/bin/env python
# coding=utf-8

import cgi
import pycurl
import StringIO
import simplejson as json
import time

API_URL = 'https://www.car2go.com/api/v2.1/vehicles?loc={loc}&oauth_consumer_key=car2gowebsite&format=json'
MAPS_URL = 'https://maps.google.ca/maps?q={q}&ll={ll}&z=16&t=h'.replace('&', '&amp;')
MAPS_IFRAME_CODE = '<iframe width="300" height="250" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" src="https://maps.google.ca/maps?q={q}&amp;ll={ll}&amp;t=m&amp;z=15&amp;output=embed"></iframe>'.replace('&', '&amp;')
MAPS_IMAGE_CODE = '<img src="http://maps.googleapis.com/maps/api/staticmap?size=300x250&zoom=15&markers=size:small|{ll}&sensor=false" alt="map of {q}" />'.replace('&', '&amp;')

CITIES = { 'amsterdam': 'Amsterdam', 'austin': 'Austin', 'berlin': 'Berlin',
	'calgary': 'Calgary', 'duesseldorf': 'Düsseldorf', 'hamburg': 'Hamburg',
	'koeln': 'Köln', 'london': 'London', 'miami': 'Miami', 'portland': 'Portland',
	'sandiego': 'San Diego', 'seattle': 'Seattle', 'stuttgart': 'Stuttgart', 
	'toronto': 'Toronto', 'ulm': 'Ulm', 'vancouver': 'Vancouver',
	'washingtondc': 'Washington, D.C.', 'wien': 'Wien'}

def get_URL(url):
	htime1 = time.time()

	c = pycurl.Curl()
	c.setopt(pycurl.URL, url)

	b = StringIO.StringIO()
	c.setopt(pycurl.WRITEFUNCTION, b.write)
	c.perform()

	htime2 = time.time()
	print '<!--http get: %0.3f ms' % ((htime2-htime1)*1000.0) + '-->'

	html = b.getvalue()
	b.close()
	
	return html

def format_car(car):
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
	mapurl = MAPS_URL.replace('{ll}', coords).replace('{q}', car['address'].replace(' ','%20'))
	info += 'Coords: <a href="' + mapurl + '">' + coords + '<br/>'

	info += MAPS_IMAGE_CODE.replace('{ll}', coords).replace('{q}', car['address'])
	info += '</a>'

	return info

def get_electric_cars(city):
	json_text = get_URL(API_URL.replace('{loc}', city))

	time1 = time.time()

	cars = json.loads(json_text).get('placemarks')

	time2 = time.time()
	print '<!--json load: %0.3f ms' % ((time2-time1)*1000.0) + '-->'

	electric_cars = []


	time1 = time.time()

	for car in cars:
		if car['engineType'] == 'ED':
			electric_cars.append(format_car(car))

	time2 = time.time()
	print '<!--list search: %0.3f ms' % ((time2-time1)*1000.0) + '-->'

	return electric_cars

def get_city():
	city = 'vancouver' # default to Vancouver

	arguments = cgi.FieldStorage()

	if 'city' in arguments:
		param = str(arguments['city'].value).lower()
		if param in CITIES:
			city = param

	return city

def get_formatted_all_cities(requested_city):
	formatted_cities = []

	for city,formatted_name in sorted(CITIES.iteritems()):
		if city == requested_city:
			formatted_cities.append('<strong>' + formatted_name + '</strong>')
		else:
			formatted_cities.append('<a href="?city=' + city + '">' + formatted_name + '</a>')

	return '<p>car2go cities: ' + ', '.join(formatted_cities)

def print_all_html():
	print 'Content-type: text/html\n'

	ttime1 = time.time()

	requested_city = get_city()

	print '<!doctype html>'
	print '<meta charset="utf-8" />'
	print '<title>electric car2go vehicles in ' + CITIES[requested_city] + '</title>'

	print get_formatted_all_cities(requested_city)

	electric_cars = get_electric_cars(requested_city)

	count = len(electric_cars)
	plural = 's' if count != 1 else ''

	print '<p>' + str(count) + ' electric car' + plural,
	print ' currently available in ' + CITIES[requested_city]

	for car in electric_cars:
		print '<p>' + car

	ttime2 = time.time()
	print '<!--total: %0.3f ms' % ((ttime2-ttime1)*1000.0) + '-->'

if __name__ == '__main__':
	print_all_html()
