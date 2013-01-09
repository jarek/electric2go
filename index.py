#!/usr/bin/env python
# coding=utf-8

import cgi
import pycurl
import StringIO
import simplejson as json
import time
import os
import sys
from datetime import datetime

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

timer = list()

def get_URL(url):
	htime1 = time.time()

	c = pycurl.Curl()
	c.setopt(pycurl.URL, url)

	b = StringIO.StringIO()
	c.setopt(pycurl.WRITEFUNCTION, b.write)
	c.perform()

	htime2 = time.time()
	timer.append(['http get', (htime2-htime1)*1000.0])

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

def get_all_cars_text(city):
	json_text = None

	cached_data_filename = './data/current_%s' % city
	if os.path.exists(cached_data_filename):
		cached_data_timestamp = os.path.getmtime(cached_data_filename)
		cached_data_age = datetime.now() - datetime.fromtimestamp(cached_data_timestamp)
		if cached_data_age.days == 0 and cached_data_age.seconds < 180:
			timer.append(['using cached data, age in seconds', cached_data_age.seconds])
			f = open(cached_data_filename, 'r')
			json_text = f.read()
			f.close()

	if json_text == None:	
		json_text = get_URL(API_URL.replace('{loc}', city))

	return json_text

def get_electric_cars(city):
	json_text = get_all_cars_text(city)

	time1 = time.time()

	cars = json.loads(json_text).get('placemarks')

	time2 = time.time()
	timer.append(['json load', (time2-time1)*1000.0])

	electric_cars = []


	time1 = time.time()

	for car in cars:
		if car['engineType'] == 'ED':
			electric_cars.append(car)

	time2 = time.time()
	timer.append(['list search', (time2-time1)*1000.0])

	return electric_cars

def get_formatted_electric_cars(city):
	electric_cars = get_electric_cars(city)
	result = []

	for car in electric_cars:
		result.append(format_car(car))

	return result

def get_city():
	city = 'vancouver' # default to Vancouver

	# look for http param first
	# if http param not present, look for command line param
	
	param = None
	arguments = cgi.FieldStorage()

	if 'city' in arguments:
		param = str(arguments['city'].value).lower()
	elif len(sys.argv) > 1:
		param = sys.argv[1].lower()

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

def print_timer_info():
	for timepoint in timer:
		print '<!--%s: %0.3f ms-->' % (timepoint[0], timepoint[1])

def print_all_html():
	print 'Content-type: text/html\n'

	ttime1 = time.time()

	requested_city = get_city()

	print '<!doctype html>'
	print '<meta charset="utf-8" />'
	print '<title>electric car2go vehicles in ' + CITIES[requested_city] + '</title>'

	print get_formatted_all_cities(requested_city)

	electric_cars = get_formatted_electric_cars(requested_city)

	count = len(electric_cars)
	plural = 's' if count != 1 else ''

	print '<p>' + str(count) + ' electric car' + plural,
	print ' currently available in ' + CITIES[requested_city]

	for car in electric_cars:
		print '<p>' + car

	ttime2 = time.time()
	timer.append(['total', (ttime2-ttime1)*1000.0])

	print_timer_info()


if __name__ == '__main__':
	print_all_html()
