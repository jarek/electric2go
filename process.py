#!/usr/bin/env python
# coding=utf-8

from datetime import datetime
from datetime import timedelta
import os
import sys
import math
import simplejson as json
import matplotlib.pyplot as plt
import numpy as np
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

# these ratios are connected
# 991/508 : (49.295-49.224)/(123.252-123.04) :: 111209.70 : 73171.77
MAP_X = 991
MAP_Y = 508

def process_data(json_data, data_time = None, previous_data = {}):
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

def map_latitude(latitudes):
	return ((latitudes - LIMIT_SOUTH)/(LIMIT_NORTH - LIMIT_SOUTH)) * MAP_Y

def map_longitude(longitudes):
	return ((longitudes - LIMIT_WEST)/(LIMIT_EAST - LIMIT_WEST)) * MAP_X

def make_graph(data, filename, turn):
	# my lists of latitudes, longitudes, will be at most
	# as lost as data (when all cars are currently being seen)
	# and usually around 1/2 - 2/3rd the size. pre-allocating 
	# zeros and keeping track of the actual size is the most 
	# memory-efficient thing to do, i think.
	# (I have to use numpy arrays to transform coordinates. 
	# and numpy array appends are not in place.)
	max_length = len(data)

	latitudes = np.empty(max_length)
	longitudes = np.empty(max_length)
	
	# lists for the lines will be usually 5-30 long or so. 
	# i'll keep them as standard python for the appends 
	# and convert later
	lines_start_lat = []
	lines_start_lng = []
	lines_end_lat = []
	lines_end_lng = []

	car_count = 0

	for car in data:
		if data[car]['seen'] == turn:
			if is_latlng_in_bounds(data[car]['coords']):
				latitudes[car_count] = data[car]['coords'][0]
				longitudes[car_count] = data[car]['coords'][1]

			car_count = car_count + 1

			# if car has just moved, add a line from previous point to current point
			if data[car]['just_moved'] == True:
				lines_start_lat.append(data[car]['prev_coords'][0])
				lines_start_lng.append(data[car]['prev_coords'][1])
				lines_end_lat.append(data[car]['coords'][0])
				lines_end_lng.append(data[car]['coords'][1])

	# translate into map coordinates
	latitudes = map_latitude(latitudes)
	longitudes = map_longitude(longitudes)

	lines_start_lat = map_latitude(np.array(lines_start_lat))
	lines_start_lng = map_longitude(np.array(lines_start_lng))
	lines_end_lat = map_latitude(np.array(lines_end_lat))
	lines_end_lng = map_longitude(np.array(lines_end_lng))
	
	# set up figure area
	dpi = 80
 	# i actually have no idea why this is necessary, but the 
	# figure sizes are wrong otherwise. ???
	dpi_adj_x = 0.775
	dpi_adj_y = 0.8

	f = plt.figure(dpi=dpi)
	f.set_size_inches(MAP_X/dpi_adj_x/dpi, MAP_Y/dpi_adj_y/dpi)

	# uncomment the second line below to include map directly in plot
	# processing makes it look a bit worse than the original map - 
	# so keeping the generated graph transparent and overlaying it 
	# on source map is a good option too
	im = plt.imread(cars.data_dir + 'map.jpg')
	#implot = plt.imshow(im, origin='lower',aspect='auto')

	plt.axis([0, MAP_X, 0, MAP_Y])

	plt.plot(longitudes, latitudes, 'b.') 
	
	# remove visible axes and figure frame
	ax = plt.gca()
	ax.axes.get_xaxis().set_visible(False)
	ax.axes.get_yaxis().set_visible(False)
	ax.set_frame_on(False)

	# add in lines for moving vehicles
	for i in range(len(lines_start_lat)):
		l = plt.Line2D([lines_start_lng[i], lines_end_lng[i]], \
			[lines_start_lat[i], lines_end_lat[i]], color='grey')
		ax.add_line(l)

	# add labels
	ax.text(10, MAP_Y - 20, city + ' ' + turn.strftime('%Y-%m-%d %H:%M'), fontsize=10)
	ax.text(10, MAP_Y - 40, 'total cars: %d' % car_count, fontsize=10)
	ax.text(10, MAP_Y - 60, 'moved this round: %d' % len(lines_start_lat), fontsize=10)

	plt.savefig(filename + '.png', bbox_inches='tight', pad_inches=0, dpi=dpi, transparent=True)

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

