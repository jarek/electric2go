#!/usr/bin/env python

import cgi
import pycurl
import StringIO
import simplejson as json

API_URL = 'https://www.car2go.com/api/v2.1/vehicles?loc={loc}&oauth_consumer_key=car2gowebsite&format=json'
MAPS_URL = 'https://maps.google.ca/maps?q={q}&ll={ll}&z=16&t=h'
MAPS_IFRAME_CODE = '<iframe width="300" height="250" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" src="https://maps.google.ca/maps?q={q}&amp;ll={ll}&amp;t=m&amp;z=15&amp;output=embed"></iframe>'

CITIES = ['amsterdam', 'austin', 'berlin', 'calgary', 'duesseldorf', 'hamburg',
	'koeln', 'london', 'miami', 'portland', 'sandiego', 'stuttgart', 
	'toronto', 'ulm', 'vancouver', 'washingtondc', 'wien']

def get_URL(url):
	c = pycurl.Curl()
	c.setopt(pycurl.URL, url)

	b = StringIO.StringIO()
	c.setopt(pycurl.WRITEFUNCTION, b.write)
	c.perform()

	html = b.getvalue()
	b.close()
	
	return html

def format_car(car):
	info = 'Location: ' + car['address'] + '<br/>'

	charge = car['fuel']
	if charge < 20:
		info += '<span color="red">Not driveable</span>, '
	else:
		range = 1.2 * charge # approx 135 km on full charge, round down
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

	info += MAPS_IFRAME_CODE.replace('{ll}', coords).replace('{q}', car['address'])

	return info

def get_electric_cars(city):
	json_text = get_URL(API_URL.replace('{loc}', city))
	cars = json.loads(json_text).get('placemarks')

	electric_cars = []

	for car in cars:
		if car['engineType'] == 'ED':
			electric_cars.append(format_car(car))

	return electric_cars

def get_city():
	arguments = cgi.FieldStorage()

	if 'city' in arguments and arguments['city'].value in CITIES:
		city = arguments['city'].value
	else:
		city = 'vancouver'

	return city


print 'Content-type: text/html\n'

city = get_city()

electric_cars = get_electric_cars(city)

count = len(electric_cars)
plural = 's' if count != 1 else ''

print '<p>' + str(count) + ' electric car' + plural,
print ' currently available in ' + city.title()

for car in electric_cars:
	print '<p>' + car

