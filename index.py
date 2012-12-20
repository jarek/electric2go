#!/usr/bin/env python

import cgi
import pycurl
import StringIO
import simplejson as json
import time

API_URL = 'https://www.car2go.com/api/v2.1/vehicles?loc={loc}&oauth_consumer_key=car2gowebsite&format=json'
MAPS_URL = 'https://maps.google.ca/maps?q={q}&ll={ll}&z=16&t=h'
MAPS_IFRAME_CODE = '<iframe width="300" height="250" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" src="https://maps.google.ca/maps?q={q}&amp;ll={ll}&amp;t=m&amp;z=15&amp;output=embed"></iframe>'
MAPS_IMAGE_CODE = '<img src="http://maps.googleapis.com/maps/api/staticmap?size=300x250&zoom=15&markers=size:small|{ll}&sensor=false" alt="map of {q}" />'

CITIES = ['amsterdam', 'austin', 'berlin', 'calgary', 'duesseldorf', 'hamburg',
	'koeln', 'london', 'miami', 'portland', 'sandiego', 'stuttgart', 
	'toronto', 'ulm', 'vancouver', 'washingtondc', 'wien']

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
	mapurl = MAPS_URL.replace('{ll}', coords).replace('{q}', car['address'])
	info += 'Coords: <a href="' + mapurl + '">' + coords + '</a><br/>'

	info += MAPS_IMAGE_CODE.replace('{ll}', coords).replace('{q}', car['address'])

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


print 'Content-type: text/html\n'

ttime1 = time.time()

city = get_city()

electric_cars = get_electric_cars(city)

count = len(electric_cars)
plural = 's' if count != 1 else ''

print '<p>' + str(count) + ' electric car' + plural,
print ' currently available in ' + city.title()

for car in electric_cars:
	print '<p>' + car

ttime2 = time.time()
print '<!--total: %0.3f ms' % ((ttime2-ttime1)*1000.0) + '-->'

