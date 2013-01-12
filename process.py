#!/usr/bin/env python
# coding=utf-8

from datetime import datetime
from datetime import timedelta
import os
import sys
import math
import simplejson as json
import cars


LIMIT_NORTH = 49.295
LIMIT_SOUTH = 49.224
LIMIT_EAST  = -123.04
LIMIT_WEST  = -123.252
# there's also parkspots in Richmond and Langley.
# I think I will ignore them to make map more compact.

def process_data(json_data, data_time = None, previous_data = {}):
	data = previous_data
	moved_cars = []
	
	for car in json_data:
		vin = car['vin']
		lat = car['coordinates'][1]
		lng = car['coordinates'][0]

		if vin in data:
			if not (data[vin]['coords'][0] == lat and data[vin]['coords'][1] == lng):
				# car has moved since last known position
				data[vin]['prev_coords'] = data[vin]['coords']
				data[vin]['prev_seen'] = data[vin]['seen']

				data[vin]['coords'] = [lat, lng]
				data[vin]['seen'] = data_time

				moved_cars.append(vin)
				
			else:
				# car has not moved from last known position. just update time last seen
				data[vin]['seen'] = data_time
		else:
			data[vin] = {'coords': [lat, lng], 'seen': data_time}

	return data,moved_cars

def make_csv(data, filename):
	text = []
	for car in data:
		[lat,lng] = data[car]['coords']
		if lat <= LIMIT_NORTH and lat >= LIMIT_SOUTH and lng >= LIMIT_WEST and lng <= LIMIT_EAST:
			text.append(car + ',' + str(lat) + ',' + str(lng))

	f = open(filename + '.csv', 'w')
	print >> f, '\n'.join(text)
	f.close()

def get_stats(car_data):
	lat_max = 40
	lat_min = 55
	long_max = -125
	long_min = -120

	for car in car_data:
		lat = car['coordinates'][1]
		lng = car['coordinates'][0]

		if lat > lat_max:
			lat_max = lat

		if lat < lat_min:
			lat_min = lat
		
		if lng > long_max:
			long_max = lng
		
		if lng < long_min:
			long_min = lng

	return lat_min, lat_max, long_min, long_max


#if len(sys.argv) > 2:
#	filename = sys.argv[2].lower()
	# TODO: this value will be ignored right now. use it to read in the starting time to analyze,
	# and maybe a couple more params for step size in minutes and amount of steps


city = cars.get_city()
t = datetime.strptime('2013-01-10--17-20', '%Y-%m-%d--%H-%M') # hardcode for now
saved_data = {}

for i in range(38):
	t = t + timedelta(0, 5*60) # look for every five minutes
	print t,
	filename = cars.filename_format % (city, t.year, t.month, t.day, t.hour, t.minute)
	f = open(cars.data_dir + filename, 'r')
	json_text = f.read()
	f.close()
	json_data = json.loads(json_text).get('placemarks')

	saved_data,moved_cars = process_data(json_data, t, saved_data)
	print 'total: %d' % len(saved_data),
	print 'moved: %02d' % len(moved_cars),
	
	stats = get_stats(json_data)
	print 'lat range: ' + str(stats[0]) + ' - ' + str(stats[1]),
	print 'lng range: ' + str(stats[2]) + ' - ' + str(stats[3])

	make_csv(saved_data, filename)

# show info for cars that had just stopped moving in the last dataset
print '\njust stopped on ' + str(t) + ':'
for vin in moved_cars:
	travel_time = saved_data[vin]['seen'] - saved_data[vin]['prev_seen']
	lat1,lng1 = saved_data[vin]['prev_coords']
	lat2,lng2 = saved_data[vin]['coords']
	dist = math.sqrt( (lat2-lat1)**2 + (lng2-lng1)**2 )
	print vin,
	print 'start: ' + str(lat1) + ',' + str(lng1),
	print 'end: ' + str(lat2) + ',' + str(lng2),
	print '\ttime: ' + str(travel_time),
	print 'distance: ' + str(dist)

