#!/usr/bin/env python
# coding=utf-8

from datetime import datetime
from datetime import timedelta
import os
import sys
import math
import simplejson as json
import matplotlib.pyplot as plt
import cars


LIMIT_NORTH = 49.295
LIMIT_SOUTH = 49.224
LIMIT_EAST  = -123.04
LIMIT_WEST  = -123.252
# there's also parkspots in Richmond and Langley.
# I think I will ignore them to make map more compact.

# these are Vancouver (latitude 49) specific. http://www.csgnetwork.com/degreelenllavcalc.html
LENGTH_OF_LATITUDE = 111209.70
LENGTH_OF_LONGITUDE = 73171.77

def process_data(json_data, data_time = None, previous_data = {}):
	#	data = previous_data
	data = previous_data
	moved_cars = []

	for car in data:
		# need to reset out status for cases where cars are picked up (and therefore disappear
		# from json_data) before two cycles of process_data. otherwise their just_moved
		# is never updated
		# if necessary, just_moved will be set to true later
		data[car]['just_moved'] = False
	
	for car in json_data:
		vin = car['vin']
		lat = car['coordinates'][1]
		lng = car['coordinates'][0]

		if vin in previous_data:
			if not (data[vin]['coords'][0] == lat and data[vin]['coords'][1] == lng):
				# car has moved since last known position
				data[vin]['prev_coords'] = data[vin]['coords']
				data[vin]['prev_seen'] = data[vin]['seen']
				data[vin]['just_moved'] = True

				data[vin]['coords'] = [lat, lng]
				data[vin]['seen'] = data_time

				moved_cars.append(vin)
				#print vin + ' moved from ' + str(data[vin]['prev_coords']) + ' to ' + str(data[vin]['coords'])
				
			else:
				# car has not moved from last known position. just update time last seen
				data[vin]['seen'] = data_time
				data[vin]['just_moved'] = False
		else:
			# 'new' car showing up, initialize it
			data[vin] = {'coords': [lat, lng], 'seen': data_time, 'just_moved': False}

	return data,moved_cars

def is_latlng_in_bounds(lat, lng = False):
	if lng == False:
		lng = lat[1]
		lat = lat[0]

	return lat <= LIMIT_NORTH and lat >= LIMIT_SOUTH and lng >= LIMIT_WEST and lng <= LIMIT_EAST

def make_csv(data, filename, turn):
	text = []
	for car in data:
		[lat,lng] = data[car]['coords']
		if data[car]['seen'] == turn and is_latlng_in_bounds(lat,lng):
			text.append(car + ',' + str(lat) + ',' + str(lng))

	f = open(filename + '.csv', 'w')
	print >> f, '\n'.join(text)
	f.close()

def make_graph(data, filename, turn):
	latitudes = []
	longitudes = []
	lines = []

	for car in data:
		if data[car]['seen'] == turn:
			if is_latlng_in_bounds(data[car]['coords']):
				latitudes.append(data[car]['coords'][0])
				longitudes.append(data[car]['coords'][1])

			#if car has just moved, add a line from previous point to current point
			if data[car]['just_moved'] == True:
				lines.append([data[car]['coords'], data[car]['prev_coords']])
	
	plt.clf() # clear figure

	plt.plot(longitudes, latitudes, 'b.') 

	plt.axis([LIMIT_WEST-0.003, LIMIT_EAST+0.003, LIMIT_SOUTH-0.003, LIMIT_NORTH+0.003])
	
	# remove visible axes and figure frame
	ax = plt.gca()
	ax.axes.get_xaxis().set_visible(False)
	ax.axes.get_yaxis().set_visible(False)
	ax.set_frame_on(False)

	# add in lines for moving vehicles
	for line in lines:
		l = plt.Line2D([line[0][1], line[1][1]], [line[0][0], line[1][0]], color='grey')
		ax.add_line(l)

	# TODO: figure out how to add this image as a background without wrecking everything else
	#im = plt.imread(cars.data_dir + 'map_squished.jpg')
	#implot = plt.imshow(im, origin='lower',aspect='auto')

	# add labels
	ax.text(LIMIT_WEST, LIMIT_NORTH-0.005, 'car2go ' + city + ' ' + turn.strftime('%Y-%m-%d %H:%M'), fontsize=10)
	ax.text(LIMIT_WEST, LIMIT_NORTH-0.009, 'total cars: %d' % len(latitudes), fontsize=10)
	ax.text(LIMIT_WEST, LIMIT_NORTH-0.013, 'moved this round: %d' % len(lines), fontsize=10)

	plt.savefig(filename + '.png', bbox_inches='tight')

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
t = datetime.strptime('2013-01-10--15-50', '%Y-%m-%d--%H-%M') # hardcode for now
saved_data = {}

for i in range(56): # full test set is 56
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

	make_csv(saved_data, filename, t)
	make_graph(saved_data, filename, t)

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

