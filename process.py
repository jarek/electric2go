#!/usr/bin/env python
# coding=utf-8

from datetime import datetime
from datetime import timedelta
import os
import sys
import argparse
import math
import simplejson as json
import matplotlib.pyplot as plt
import numpy as np
import cars


KNOWN_CITIES = ['toronto', 'vancouver']

MAP_LIMITS = {
	'toronto': {
		'NORTH': 43.72736,
		'SOUTH': 43.625893,
		'EAST': -79.2768,
		'WEST': -79.50168
	},
	'vancouver': {
		# according to home area json, this is actually
		# (49.295673, 49.224716, -123.04207, -123.21545)
		# but I've picked out map sizes and everything according to the
		# coordinates below, so i'll keep them for now, at least until
		# a major update of Vancouver-specific code
		'NORTH': 49.295,
		'SOUTH': 49.224,
		'EAST':  -123.04,
		'WEST':  -123.252
		# there's also parkspots in Richmond and Langley.
		# I think I will ignore them to make map more compact.
	}
}

DEGREE_LENGTHS = {
	# from http://www.csgnetwork.com/degreelenllavcalc.html
	# could calculate ourselves but meh. would need city's latitude
	'toronto': {
		# for latitude 43.7
		'LENGTH_OF_LATITUDE': 111106.36,
		'LENGTH_OF_LONGITUDE': 80609.20
	},
	'vancouver': {
		# for latitude 49.25
		'LENGTH_OF_LATITUDE': 111214.54,
		'LENGTH_OF_LONGITUDE': 72804.85
	}
}

MAP_SIZES = {
	# all these ratios are connected
	'toronto': {
		# 615/991 / (43.72736-43.625893)/(79.50168-79.2768) ~= 111106.36 / 80609.20
		# 0.620585267 / 0.451205087 = 1.375395103 ~= 1.37833349
		'MAP_X' : 991,
		'MAP_Y' : 615
	},
	'vancouver': {
		# 508/991 / (49.295-49.224)/(123.252-123.04) ~= 111214.54 / 72804.85
		# 0.512613522 / 0.33490566 = 1.530620659 ~= 1.527570485
		'MAP_X' : 991,
		'MAP_Y' : 508
	}
}

LABELS = {
	'toronto': {
		# TODO: needs verified values
		'fontsize': 10,
		'lines': [
			(10, MAP_SIZES['toronto']['MAP_Y'] - 20),
			(10, MAP_SIZES['toronto']['MAP_Y'] - 40),
			(10, MAP_SIZES['toronto']['MAP_Y'] - 60)
		]
	},
	'vancouver': {
		'fontsize': 10,
		'lines': [
			(10, MAP_SIZES['vancouver']['MAP_Y'] - 20),
			(10, MAP_SIZES['vancouver']['MAP_Y'] - 40),
			(10, MAP_SIZES['vancouver']['MAP_Y'] - 60)
		]
	}
}


def process_data(json_data, data_time = None, previous_data = {}):
	data = previous_data
	moved_cars = []

	for car in data:
		# need to reset out status for cases where cars are picked up 
		# (and therefore disappear from json_data) before two cycles 
		# of process_data. otherwise their just_moved is never updated.
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

def find_clusters():
	# TODO: find clusters of close-by cars (for n cars within a d radius
	# or something) and graph the clusters. preferably over time.
	# knn maybe?
	# I notice spots where cars tend to gather - this might be clearer
	# to see on a map showing just the cars within the hotspots rather
	# than all cars.

	# make_graph() should be able to use the data as-is, or with minor 
	# changes. mark just_moved as False for all cars to prevent trip lines
	# from being drawn (except possibly for cars moving directly between
	# clusters?)

	pass

def is_latlng_in_bounds(city, lat, lng = False):
	if lng == False:
		lng = lat[1]
		lat = lat[0]

	# TODO: currently these are north- and west-hemisphere specific
	is_lat = MAP_LIMITS[city]['SOUTH'] <= lat <= MAP_LIMITS[city]['NORTH']
	is_lng = MAP_LIMITS[city]['WEST'] <= lng <= MAP_LIMITS[city]['EAST']

	return is_lat and is_lng

def make_csv(data, city, filename, turn):
	text = []
	for car in data:
		[lat,lng] = data[car]['coords']
		if data[car]['seen'] == turn \
			and is_latlng_in_bounds(city, lat, lng):
			text.append(car + ',' + str(lat) + ',' + str(lng))

	f = open(filename + '.csv', 'w')
	print >> f, '\n'.join(text)
	f.close()

def map_latitude(city, latitudes):
	return ((latitudes - MAP_LIMITS[city]['SOUTH']) / \
		(MAP_LIMITS[city]['NORTH'] - MAP_LIMITS[city]['SOUTH'])) * \
		MAP_SIZES[city]['MAP_Y']

def map_longitude(city, longitudes):
	return ((longitudes - MAP_LIMITS[city]['WEST']) / \
		(MAP_LIMITS[city]['EAST'] - MAP_LIMITS[city]['WEST'])) * \
		MAP_SIZES[city]['MAP_X']

def make_graph(data, city, filename, turn, iteration = False, show_move_lines = True):
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
			if is_latlng_in_bounds(city, data[car]['coords']):
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
	latitudes = map_latitude(city, latitudes)
	longitudes = map_longitude(city, longitudes)

	lines_start_lat = map_latitude(city, np.array(lines_start_lat))
	lines_start_lng = map_longitude(city, np.array(lines_start_lng))
	lines_end_lat = map_latitude(city, np.array(lines_end_lat))
	lines_end_lng = map_longitude(city, np.array(lines_end_lng))
	
	# set up figure area
	dpi = 80
 	# i actually have no idea why this is necessary, but the 
	# figure sizes are wrong otherwise. ???
	dpi_adj_x = 0.775
	dpi_adj_y = 0.8

	f = plt.figure(dpi=dpi)
	f.set_size_inches(MAP_SIZES[city]['MAP_X']/dpi_adj_x/dpi, \
			MAP_SIZES[city]['MAP_Y']/dpi_adj_y/dpi)

	# uncomment the second line below to include map directly in plot
	# processing makes it look a bit worse than the original map - 
	# so keeping the generated graph transparent and overlaying it 
	# on source map is a good option too
	#im = plt.imread(cars.data_dir + 'background.jpg')
	#implot = plt.imshow(im, origin='lower',aspect='auto')

	plt.axis([0, MAP_SIZES[city]['MAP_X'], 0, MAP_SIZES[city]['MAP_Y']])

	plt.plot(longitudes, latitudes, 'b.') 
	
	# remove visible axes and figure frame
	ax = plt.gca()
	ax.axes.get_xaxis().set_visible(False)
	ax.axes.get_yaxis().set_visible(False)
	ax.set_frame_on(False)

	# add in lines for moving vehicles
	if show_move_lines:
		for i in range(len(lines_start_lat)):
			l = plt.Line2D([lines_start_lng[i], lines_end_lng[i]], \
				[lines_start_lat[i], lines_end_lat[i]], color='grey')
			ax.add_line(l)

	# add labels
	fontsize = LABELS[city]['fontsize']
	ax.text(LABELS[city]['lines'][0][0], LABELS[city]['lines'][0][1], \
		cars.CITIES[city]['display'] + ' ' + \
		turn.strftime('%Y-%m-%d %H:%M'), fontsize=fontsize)
	ax.text(LABELS[city]['lines'][1][0], LABELS[city]['lines'][1][1], \
		'available cars: %d' % car_count, fontsize=fontsize)
	ax.text(LABELS[city]['lines'][2][0], LABELS[city]['lines'][2][1], \
		'moved this round: %d' % len(lines_start_lat), fontsize=fontsize)

	plt.savefig(filename + '.png', bbox_inches='tight', pad_inches=0, 
		dpi=dpi, transparent=True)

	# also save with iterative filenames for ease of animation
	if not iteration == False:
		plt.savefig(filename[:filename.rfind('--')] + '_' + str(iteration).rjust(3, '0') + '.png', 
			bbox_inches='tight', pad_inches=0, 
			dpi=dpi, transparent=True)
	

def get_stats(car_data):
	# TODO: localize this, these are vancouver specific
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

def batch_process(city, starting_time, make_iterations = True, \
	show_move_lines = True, max_files = False, append_data_dir = True):

	def get_filepath(city, t, append_data_dir):
		filename = cars.filename_format % (city, t.year, t.month, t.day, t.hour, t.minute)

		if append_data_dir:
			return cars.data_dir + filename
		else:
			return filename

	i = 1
	t = starting_time
	filepath = get_filepath(city, starting_time, append_data_dir)

	saved_data = {}

	# loop as long as new files exist
	# if we have a limit specified, loop only until limit is reached
	while os.path.exists(filepath) and (max_files is False or i <= max_files):
		print t,

		f = open(filepath, 'r')
		json_text = f.read()
		f.close()
		json_data = json.loads(json_text).get('placemarks')

		saved_data,moved_cars = process_data(json_data, t, saved_data)
		print 'total known: %d' % len(saved_data),
		print 'moved: %02d' % len(moved_cars),
		
		stats = get_stats(json_data)
		#print 'lat range: ' + str(stats[0]) + ' - ' + str(stats[1]),
		#print 'lng range: ' + str(stats[2]) + ' - ' + str(stats[3])
		print

		#make_csv(saved_data, city, filepath, t)
		make_graph(saved_data, city, filepath, t, 
			iteration = make_iterations and i, 
			show_move_lines = show_move_lines)

		# next, look five minutes from now
		i = i + 1
		t = t + timedelta(0, 5*60)
		filepath = get_filepath(city, t, append_data_dir)

	# print animation information if applicable
	if make_iterations:
		# move 5 minutes back in case we ended at midnight and would
		# have wrong date on the files
		filenames = get_filepath(city, t - timedelta(0, 5*60), \
			append_data_dir)
		filenames = filenames[:filenames.rfind('--')] + '_%03d.png'

		print '\nto animate:'
		print '''avconv -loop 1 -r 8 -i background.png -vf 'movie=%s [over], [in][over] overlay' -b 1920000 -frames %d out.mp4''' % (filenames, i-1)

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

	pass

def process_commandline():
	parser = argparse.ArgumentParser()
	parser.add_argument('starting_filename', type=str,
		help='name of first file to process')
	parser.add_argument('-noiter', '--no-iter', action='store_true', 
		help='do not create iterative-named files intended to make animating easier')
	parser.add_argument('-nolines', '--no-lines', action='store_true',
		help='do not show lines indicating cars\' moves')
	parser.add_argument('-max', '--max-files', type=int, default=False,
		help='limit maximum amount of files to process')

	args = parser.parse_args()

	filename = args.starting_filename.lower()

	append_data_dir = True

	if not os.path.exists(cars.data_dir + filename):
		if not os.path.exists(filename):
			print 'file not found: ' + filename
			return 
		else:
			append_data_dir = False

	city,starting_time = filename.split('_', 1)

	# strip off directory, if any. might not work on Windows :D D:
	city = city.split('/')[-1]

	if not city in KNOWN_CITIES:
		print 'unsupported city: ' + city
		return

	try:
		# parse out starting time
		starting_time = datetime.strptime(starting_time, '%Y-%m-%d--%H-%M')
	except:
		print 'time format not recognized: ' + filename
		return

	batch_process(city, starting_time, \
		make_iterations = not args.no_iter, \
		show_move_lines = not args.no_lines, \
		max_files = args.max_files, \
		append_data_dir = append_data_dir)


if __name__ == '__main__':
	process_commandline()

