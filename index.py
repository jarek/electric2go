#!/usr/bin/env python

import pycurl, StringIO, simplejson as json, urllib

APIurl = 'https://www.car2go.com/api/v2.1/vehicles?loc=vancouver&oauth_consumer_key=car2gowebsite&format=json'

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
	info += 'Charge: ' + str(car['fuel']) + '%'
	if car['charging']:
		info += ', charging<br/>'
	else:
		info += '<br/>'
	info += 'Plate: ' + car['name'] + '<br/>'
	info += 'Interior: ' + car['interior'] + \
		', exterior: ' + car['exterior'] + '<br/>'
	info += 'Coords: ' + str(car['coordinates'][0]) + ',' \
		+ str(car['coordinates'][1]) + '<br/>'

	return info

def get_electric_cars():
	json_text = get_URL(APIurl)
	cars = json.loads(json_text).get('placemarks')

	electric_cars = []

	for car in cars:
		if car['engineType'] == 'ED':
			electric_cars.append(format_car(car))

	return electric_cars


print 'Content-type: text/html\n'

electric_cars = get_electric_cars()

count = len(electric_cars)
plural = 's' if count > 1 else ''

print '<p>' + str(count) + ' electric car' + plural + ' currently available in Vancouver'

for car in electric_cars:
	print '<p>' + car

