#!/usr/bin/env python2
# coding=utf-8

from datetime import datetime
from datetime import timedelta
import os
import sys
import stat
import argparse
import math
import copy
import time
import shutil
import simplejson as json
import matplotlib.pyplot as plt
import numpy as np
#import scipy.stats as sps
from collections import Counter
from random import choice
import Image
import cars


KNOWN_CITIES = ['austin', 'calgary', 'portland', 'seattle', 'toronto', 'vancouver', 'wien']

BOUNDS = {
    'austin': {
        'NORTH': 30.368, # exact value 30.367937, or 30.400427 incl The Domain
        'SOUTH': 30.212, # exact value 30.212427
        'EAST': -97.672, # exact value -97.672966
        'WEST': -97.804  # exact value -97.803764
    },
    'berlin': {
        # rudimentary values for testing is_latlng_in_bounds function
        'NORTH': 53,
        'SOUTH': 52,
        'EAST': 14,
        'WEST': 13
    },
    'buenosaires': {
        # rudimentary values for an unsupported city for testing
        'NORTH': -34,
        'SOUTH': -35,
        'EAST': -58,
        'WEST': -59
    },
    'calgary': {
        'NORTH': 51.088425,
        'SOUTH': 50.984936,
        'EAST': -113.997314,
        'WEST': -114.16401
    },
    'montreal': {
        'NORTH': 45.584, # exact value is 45.58317
        'SOUTH': 45.452, # exact value is 45.452515
        'EAST': -73.548, # exact value is -73.548615
        'WEST': -73.662 # exact value is -73.661095
    },
    'portland': {
        'NORTH': 45.583, # exact value is 45.582718
        'SOUTH': 45.435, # exact value is 45.435555, or 45.463924 excl PCC
        'EAST': -122.557, # exact value is -122.557724
        'WEST': -122.738 # exact value is -122.73726, or -122.72915 excl PCC
    },
    'seattle': {
        'NORTH': 47.724, # exact value is 47.723562
        'SOUTH': 47.520, # exact value is 47.5208 - Fauntleroy Ferry
        'EAST': -122.245, # exact value is -122.24517
        'WEST': -122.437 # exact value is -122.43666
    },
    'toronto': {
        'NORTH': 43.72736,
        'SOUTH': 43.625893,
        'EAST': -79.2768,
        'WEST': -79.50168
    },
    'vancouver': {
        'NORTH': 49.336, # exact value 49.335735
        'SOUTH': 49.224, # exact value 49.224716
        'EAST':  -123.031, # exact value -123.03196
        'WEST':  -123.252
        # limit of home area is -123.21545; westernmost parking spot 
        # at UBC is listed as centered on -123.2515
        
        # there's also parkspots in Richmond and Langley,
        # I am ignoring them to make map more compact.
    },
    'wien': {
        'NORTH': 48.29633,
        'SOUTH': 48.14736,
        'EAST': 16.48181,
        'WEST': 16.279331
        # excluded parkspots outside of main home area and at airport
    }
}

MAP_LIMITS = {
    'austin': {
        # values are different than home area bounds - 16:9 aspect ratio
        # map scale is 1:99776
        'NORTH': 30.368,
        'SOUTH': 30.212,
        'EAST': -97.5774,
        'WEST': -97.8986
    },
    'berlin': {
        # rudimentary values for testing is_latlng_in_bounds function
        'NORTH': 53,
        'SOUTH': 52,
        'EAST': 14,
        'WEST': 13
    },
    'buenosaires': {
        # rudimentary values for an unsupported city for testing
        'NORTH': -34,
        'SOUTH': -35,
        'EAST': -58,
        'WEST': -59
    },
    'calgary': {
        'NORTH': 51.088425,
        'SOUTH': 50.984936,
        'EAST': -113.997314,
        'WEST': -114.16401
    },
    'montreal': {
        # E&W values are different than home area bounds - 16:9 aspect ratio
        # map scale is 69333 for 1920x1080
        # http://parent.tile.openstreetmap.org/cgi-bin/export?bbox=-73.7725,45.452,-73.4375,45.584&scale=69333&format=png
        'NORTH': 45.584,
        'SOUTH': 45.452,
        'EAST': -73.4375,
        'WEST': -73.7725
    },
    'portland': {
        # values are different than home area bounds - 16:9 aspect ratio
        # map scale is 1:77700 for 1920x1080, 116500 for 1280x720
        # http://parent.tile.openstreetmap.org/cgi-bin/export?bbox=-122.83514,45.435,-122.45986,45.583&scale=116500&format=png for 1280x720
        # http://parent.tile.openstreetmap.org/cgi-bin/export?bbox=-122.83514,45.435,-122.45986,45.583&scale=77700&format=png for 1920x1080
        'NORTH': 45.583,
        'SOUTH': 45.435,
        'EAST': -122.45986,
        'WEST': -122.83514
    },
    'seattle': {
        # values are different than home area bounds - 16:9 aspect ratio
        # map scale is 1 : 111350 for 1920x1080
        # http://parent.tile.openstreetmap.org/cgi-bin/export?bbox=-122.61,47.52,-122.072,47.724&scale=111300&format=png
        'NORTH': 47.724,
        'SOUTH': 47.520,
        'EAST': -122.072,
        'WEST': -122.610
    },
    'toronto': {
        'NORTH': 43.72736,
        'SOUTH': 43.625893,
        'EAST': -79.2768,
        'WEST': -79.50168
    },
    'vancouver': {
        # E & W values are different than home area bounds - 16:9 aspect ratio
        # map scale is 1 : 63200 for 1920x1080
        # http://parent.tile.openstreetmap.org/cgi-bin/export?bbox=-123.29415,49.224,-122.98885,49.336&scale=63200&format=png
        'NORTH': 49.336,
        'SOUTH': 49.224,
        'EAST':  -122.98885,
        'WEST':  -123.29415
    },
    'wien': {
        # E&W values are different than home area bounds - 16:9 aspect ratio
        # map scale is 82237 for 1920x1080
        # http://parent.tile.openstreetmap.org/cgi-bin/export?bbox=16.181987,48.1474,16.579154,48.2963&scale=82237&format=png
        'NORTH': 48.29633,
        'SOUTH': 48.14736,
        'EAST': 16.579154,
        'WEST': 16.181987
    }
}

DEGREE_LENGTHS = {
    # from http://www.csgnetwork.com/degreelenllavcalc.html
    # could calculate ourselves but meh. would need city's latitude
    'austin': {
        # for latitude 30.29
        'LENGTH_OF_LATITUDE': 110857.33,
        'LENGTH_OF_LONGITUDE': 96204.48
    },
    'calgary': {
        # for latitude 51.04
        'LENGTH_OF_LATITUDE': 111249.00,
        'LENGTH_OF_LONGITUDE': 70137.28
    },
    'portland': {
        # for latitude 45.52
        'LENGTH_OF_LATITUDE': 111141.91,
        'LENGTH_OF_LONGITUDE': 78130.36
    },
    'seattle': {
        # for latitude 47.61
        'LENGTH_OF_LATITUDE': 111182.70,
        'LENGTH_OF_LONGITUDE': 75186.03
    },
    'toronto': {
        # for latitude 43.7
        'LENGTH_OF_LATITUDE': 111106.36,
        'LENGTH_OF_LONGITUDE': 80609.20
    },
    'vancouver': {
        # for latitude 49.28
        'LENGTH_OF_LATITUDE': 111215.12,
        'LENGTH_OF_LONGITUDE': 72760.72
    },
    'wien': {
        # for latitude 48.22
        'LENGTH_OF_LATITUDE': 111194.56,
        'LENGTH_OF_LONGITUDE': 74307.49
    }
}

MAP_SIZES = {
    # all these ratios are connected
    'austin': {
        # 720/1280 / (30.368-30.212)/(97.8986-97.5774) ~= 110857.33 / 96204.48
        # 0.5625 / 0.485678705 = 1.158173077 ~= 1.152309435
        'MAP_X': 1280,
        'MAP_Y': 720
    },
    'berlin': {
        # fake values for testing
        'MAP_X': 991,
        'MAP_Y': 800
    },
    'calgary': {
        # 978/991 / (51.088425-50.984936)/(114.16401-113.997314) ~= 111249.00 / 70137.28
        # 0.986881937 / 0.620824735 = 1.589630505 ~= 1.586160741
        'MAP_X': 991,
        'MAP_Y': 978
    },
    'portland': {
        # 1080/1920 / (45.583-45.435)/(122.83514-122.45986) ~= 111141.91 / 78130.36
        # 0.5625 / 0.394372202 = 1.426317568 ~= 1.422518852
        'MAP_X': 1920,
        'MAP_Y': 1080,
    },
    'seattle': {
        # 1080/1920 / (47.724-47.520)/(122.610-122.072) ~= 111182.70 / 75186.03
        # 0.5625 / 0.379182156 = 1.483455883 ~= 1.478768064
        'MAP_X' : 1920,
        'MAP_Y' : 1080
    },
    'toronto': {
        # 615/991 / (43.72736-43.625893)/(79.50168-79.2768) ~= 111106.36 / 80609.20
        # 0.620585267 / 0.451205087 = 1.375395103 ~= 1.37833349
        'MAP_X' : 991,
        'MAP_Y' : 615
    },
    'vancouver': {
        # 1080/1920 / (49.336-49.224)/(123.29415-122.98885) ~= 111215.12 / 72760.72
        # 0.5625 / 0.366852276 = 1.533314734 ~= 1.528504941
        'MAP_X' : 1920,
        'MAP_Y' : 1080
    },
    'wien': {
        'MAP_X': 1920,
        'MAP_Y': 1080
    }
}

LABELS = {
    'austin': {
        'fontsizes': [30, 22, 30, 18, 18],
        'lines': [
            (20, MAP_SIZES['austin']['MAP_Y']-50),
            (20, MAP_SIZES['austin']['MAP_Y']-82),
            (20, MAP_SIZES['austin']['MAP_Y']-122),
            (20, MAP_SIZES['austin']['MAP_Y']-155),
            (20, MAP_SIZES['austin']['MAP_Y']-180)
        ]
    },
    'calgary': {
        'fontsize': 15,
        'lines': [
            (MAP_SIZES['calgary']['MAP_X']*0.75,
                    MAP_SIZES['calgary']['MAP_Y']-120),
            (MAP_SIZES['calgary']['MAP_X']*0.75,
                    MAP_SIZES['calgary']['MAP_Y']-145),
            (MAP_SIZES['calgary']['MAP_X']*0.75,
                    MAP_SIZES['calgary']['MAP_Y']-170)
        ]
    },
    'portland': {
        'fontsizes': [30, 22, 30, 18, 18],
        'lines': [
            (20, MAP_SIZES['portland']['MAP_Y']-50),
            (20, MAP_SIZES['portland']['MAP_Y']-82),
            (20, MAP_SIZES['portland']['MAP_Y']-122),
            (20, MAP_SIZES['portland']['MAP_Y']-155),
            (20, MAP_SIZES['portland']['MAP_Y']-180)
        ]
    },
    'seattle': {
        'fontsizes': [35, 22, 30, 18, 18],
        'lines': [
            (400, MAP_SIZES['seattle']['MAP_Y']-55),
            (400, MAP_SIZES['seattle']['MAP_Y']-93),
            (400, MAP_SIZES['seattle']['MAP_Y']-132),
            (400, MAP_SIZES['seattle']['MAP_Y']-170),
            (400, MAP_SIZES['seattle']['MAP_Y']-195)
        ]
    },
    'toronto': {
        'fontsize': 15,
        'lines': [
            (MAP_SIZES['toronto']['MAP_X'] * 0.75, 160),
            (MAP_SIZES['toronto']['MAP_X'] * 0.75, 130),
            (MAP_SIZES['toronto']['MAP_X'] * 0.75, 100)
        ]
    },
    'vancouver': {
        'fontsizes': [35, 22, 30, 18, 18],
        'lines': [
            (20, MAP_SIZES['vancouver']['MAP_Y']-55),
            (20, MAP_SIZES['vancouver']['MAP_Y']-93),
            (20, MAP_SIZES['vancouver']['MAP_Y']-132),
            (20, MAP_SIZES['vancouver']['MAP_Y']-170),
            (20, MAP_SIZES['vancouver']['MAP_Y']-195)
        ]
    },
    'wien': {
        'fontsizes': [35, 22, 30, 18, 18],
        'lines': [
            (200, MAP_SIZES['wien']['MAP_Y']-55),
            (200, MAP_SIZES['wien']['MAP_Y']-93),
            (200, MAP_SIZES['wien']['MAP_Y']-132),
            (200, MAP_SIZES['wien']['MAP_Y']-170),
            (200, MAP_SIZES['wien']['MAP_Y']-195)
        ]
    }
}

# speed ranges are designated as: 0-5; 5-15; 15-30; 30+
SPEED_CUTOFFS = [5, 15, 30, float('inf')]
SPEED_COLOURS = ['r', 'y', 'g', 'b']

timer = []
DEBUG = False


def process_data(json_data, data_time = None, previous_data = {}, \
    show_speeds = False, hold_for = 0, **extra_args):

    args = locals()
    
    def dist(ll1, ll2):
        # adapted from http://www.movable-type.co.uk/scripts/latlong.html
        # see also http://stackoverflow.com/questions/27928/how-do-i-calculate-distance-between-two-latitude-longitude-points
        # the js equivalent is used in sort.js - any changes
        # should be reflected in both
        def deg2rad(deg):
            return deg * (math.pi/180.0)

        R = 6371 # Radius of the earth in km
        dLat = deg2rad(ll2[0]-ll1[0])
        dLon = deg2rad(ll2[1]-ll1[1])

        a = math.sin(dLat/2) * math.sin(dLat/2) + \
            math.cos(deg2rad(ll1[0])) * math.cos(deg2rad(ll2[0])) * \
            math.sin(dLon/2) * math.sin(dLon/2)

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        d = R * c # Distance in km
        return d

    data = previous_data
    moved_cars = []

    for vin in data.keys():
        # if requested, save old state first, for up to HOLD_ON copies
        if hold_for > 0 and vin.find('_') < 0:
            # first move cache items back. 1 becomes 2, 0 becomes 1
            for i in reversed(range(1, hold_for)):
                # for hold_for=3 will do 2,1
                curr = str(i) + '_' + vin # current key
                prev = str(i-1) + '_' + vin # previous key

                if prev in data:
                    data[curr] = copy.deepcopy(data[prev])
            
            # then 0 comes straight from the vehicle being cached
            data['0_' + vin] = copy.deepcopy(data[vin])
    
        # need to reset out status for cases where cars are picked up 
        # (and therefore disappear from json_data) before two cycles 
        # of process_data. otherwise their just_moved is never updated.
        # if necessary, just_moved will be set to true later
        if vin.find('_') < 0:
            # except exclude 'held' points from just_moved clearing
            data[vin]['just_moved'] = False

    for car in json_data:
        if 'vin' in car:
            vin = car['vin']
            name = car['name']
            lat = car['coordinates'][1]
            lng = car['coordinates'][0]
            time = data_time
        elif 'VehicleNo' in car:
            vin = car['VehicleNo']
            name = car['VehicleNo']
            lat = car['Latitude']
            lng = car['Longitude']
            time = datetime.strptime(car['RecordedTime'], \
                '%I:%M:%S %p')
        else:
            # no recognized data in this file
            continue

        if vin in previous_data:
            if not (data[vin]['coords'][0] == lat and data[vin]['coords'][1] == lng):
                # car has moved since last known position
                data[vin]['prev_coords'] = data[vin]['coords']
                data[vin]['prev_seen'] = data[vin]['seen']
                data[vin]['coords'] = [lat, lng]
                data[vin]['seen'] = time
                data[vin]['just_moved'] = True

                if 'fuel' in data[vin]:
                    data[vin]['prev_fuel'] = data[vin]['fuel']
                    data[vin]['fuel'] = car['fuel']
                    data[vin]['fuel_use'] = data[vin]['prev_fuel'] - car['fuel']

                data[vin]['distance'] = dist(data[vin]['coords'], data[vin]['prev_coords'])
                t_span = time - data[vin]['prev_seen']
                data[vin]['duration'] = t_span.total_seconds()

                trip_data = {
                    'vin': vin,
                    'from': data[vin]['prev_coords'],
                    'to': data[vin]['coords'],
                    'starting_time': data[vin]['prev_seen'],
                    'ending_time': data[vin]['seen'],
                    'distance': data[vin]['distance'],
                    'duration': data[vin]['duration'],
                    'fuel_use': 0
                    }
                if 'fuel' in data[vin]:
                    trip_data['starting_fuel'] = data[vin]['prev_fuel']
                    trip_data['ending_fuel'] = data[vin]['fuel']
                    trip_data['fuel_use'] = data[vin]['fuel_use']

                data[vin]['trips'].append(trip_data)

                if t_span.total_seconds() > 0:
                    t_span = t_span.total_seconds() / 3600.0
                    data[vin]['speed'] = data[vin]['distance'] / t_span

                moved_cars.append(vin)
                
            else:
                # car has not moved from last known position. just update time last seen
                data[vin]['seen'] = time
                data[vin]['just_moved'] = False
        else:
            # 'new' car showing up, initialize it
            data[vin] = {'name': name, 'coords': [lat, lng], 'seen': time,
                'just_moved': False, 'trips': []}
            if 'fuel' in car:
                data[vin]['fuel'] = car['fuel']

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

    is_lat = BOUNDS[city]['SOUTH'] <= lat <= BOUNDS[city]['NORTH']
    is_lng = BOUNDS[city]['WEST'] <= lng <= BOUNDS[city]['EAST']

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

def make_graph_axes(city, background = False, log_name = ''):
    """ Sets up figure area and axes for common properties for a city 
    to be graphed. The param `log_name` is used for logging only. """

    # set up figure area

    global timer

    time_plotsetup_start = time.time()
    
    dpi = 80
    # i actually have no idea why this is necessary, but the 
    # figure sizes are wrong otherwise. ???
    dpi_adj_x = 0.775
    dpi_adj_y = 0.8

    # TODO: the two below take ~20 ms. try to reuse
    f = plt.figure(dpi=dpi)
    f.set_size_inches(MAP_SIZES[city]['MAP_X']/dpi_adj_x/dpi, \
            MAP_SIZES[city]['MAP_Y']/dpi_adj_y/dpi)

    # TODO: this takes 50 ms each time. try to reuse the whole set of axes
    # rather than regenerating it each time
    ax = f.add_subplot(111)
    ax.axis([0, MAP_SIZES[city]['MAP_X'], 0, MAP_SIZES[city]['MAP_Y']])

    # remove visible axes and figure frame
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)
    ax.set_frame_on(False)

    if isinstance(background, basestring) and os.path.exists(background):
        # matplotlib's processing makes the image look a bit worse than 
        # the original map - so keeping the generated graph transparent 
        # and overlaying it on source map post-render is a good option too
        background = plt.imread(background)

    if background:
        implot = ax.imshow(background, origin = 'lower', aspect = 'auto')

    timer.append((log_name + ': make_graph_axes, ms',
        (time.time()-time_plotsetup_start)*1000.0))

    return f,ax

def make_graph_object(data, city, turn, show_move_lines = True, \
    show_speeds = False, symbol = '.', log_name = '', background = False,
    time_offset = 0,
    **extra_args):
    """ Creates and returns the matplotlib figure for the provided data.
    The param `log_name` is used for logging only. """

    args = locals()

    # my lists of latitudes, longitudes, will be at most
    # as lost as data (when all cars are currently being seen)
    # and usually around 1/2 - 2/3rd the size. pre-allocating 
    # zeros and keeping track of the actual size is the most 
    # memory-efficient thing to do, i think.
    # (I have to use numpy arrays to transform coordinates. 
    # and numpy array appends are not in place.)
    global timer
    time_init_start = time.time()

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

    speeds = []
    for i in range(len(SPEED_CUTOFFS)):
        # create the necessary amount of [lat, lng] baskets
        speeds.append( [ [], [] ] )

    car_count = 0

    timer.append((log_name + ': make_graph init, ms',
        (time.time()-time_init_start)*1000.0))

    time_load_start = time.time()

    for car in data:
        if data[car]['seen'] == turn or data[car]['just_moved']:
            # The second condition is for buses, where positions
            # are not logged exactly on the turn. 
            # Since they're pretty much continuously moving except
            # in really really bad traffic, this is an acceptable
            # workaround.
            # Note that cars that aren't moving have just_moved 
            # set to false in process_data.
            if is_latlng_in_bounds(city, data[car]['coords']):
                latitudes[car_count] = data[car]['coords'][0]
                longitudes[car_count] = data[car]['coords'][1]

                if 'speed' in data[car]:
                    # find the right speed basket
                    i = 0
                    while i < len(speeds):
                        if data[car]['speed'] < SPEED_CUTOFFS[i]:
                            speeds[i][0].append(data[car]['coords'][0])
                            speeds[i][1].append(data[car]['coords'][1])
                            i = len(speeds) # break loop
                        else:
                            i = i + 1

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

    if show_speeds:
        for i in range(len(speeds)):
            speeds[i][0] = map_latitude(city, np.array(speeds[i][0]))
            speeds[i][1] = map_longitude(city, np.array(speeds[i][1]))

    timer.append((log_name + ': make_graph load, ms',
        (time.time()-time_load_start)*1000.0))

    f,ax = make_graph_axes(city, background, log_name)

    time_plot_start = time.time()

    if show_speeds is False:
        ax.plot(longitudes, latitudes, 'b' + symbol)
    else:
        for i in range(len(speeds)):
            # TODO: try to plot those with on bottom, under newer 
            # points. might require changes a couple of lines above
            # instead. reverse alphabetical sort by key?
            ax.plot(speeds[i][1], speeds[i][0], SPEED_COLOURS[i] + symbol)

    # add in lines for moving vehicles
    if show_move_lines:
        for i in range(len(lines_start_lat)):
            l = plt.Line2D([lines_start_lng[i], lines_end_lng[i]], \
                [lines_start_lat[i], lines_end_lat[i]], color = '#aaaaaa')
            ax.add_line(l)

    # add labels
    printed_time = turn + timedelta(0, time_offset*3600)
    if 'fontsizes' in LABELS[city]:
        # gradual transition to new labelling format - only for cities 
        # that have fontsizes array defined

        coords = LABELS[city]['lines']
        fontsizes = LABELS[city]['fontsizes']

        ax.text(coords[0][0], coords[0][1], 
            cars.CITIES[city]['display'], fontsize = fontsizes[0])
        ax.text(coords[1][0], coords[1][1],
            printed_time.strftime('%B %d, %Y').replace(' 0',' '),
            fontsize = fontsizes[1])
        # the .replace gets rid of leading zeros in day numbers.
        # it's a bit of a hack but it works with no false positives
        # until we get a year beginning with a zero, which shouldn't be 
        # a problem for a while
        ax.text(coords[2][0], coords[2][1], 
            printed_time.strftime('%A, %H:%M'), fontsize = fontsizes[2])
        ax.text(coords[3][0], coords[3][1], 
            'available cars: %d' % car_count, fontsize = fontsizes[3])
        # TODO: maybe have an option to include this
        #ax.text(coords[4][0], coords[4][1], 'moved this round: %d' % 
        #    len(lines_start_lat), fontsize = fontsizes[4])
    else:
        fontsize = LABELS[city]['fontsize']
        ax.text(LABELS[city]['lines'][0][0], LABELS[city]['lines'][0][1], \
            cars.CITIES[city]['display'] + ' ' + \
            printed_time.strftime('%Y-%m-%d %H:%M'), fontsize=fontsize)
        ax.text(LABELS[city]['lines'][1][0], LABELS[city]['lines'][1][1], \
            'available cars: %d' % car_count, fontsize=fontsize)
        ax.text(LABELS[city]['lines'][2][0], LABELS[city]['lines'][2][1], \
            'moved this round: %d' % len(lines_start_lat), fontsize=fontsize)

    timer.append((log_name + ': make_graph plot, ms',
        (time.time()-time_plot_start)*1000.0))

    return f,ax

def make_graph(data, city, first_filename, turn, second_filename = False, \
    show_move_lines = True, show_speeds = False, symbol = '.', \
    background = False, time_offset = 0, \
    **extra_args):
    """ Creates and saves matplotlib figure for provided data. 
    If second_filename is specified, also copies the saved file to 
    second_filename. """

    args = locals()

    global timer

    time_total_start = time.time()

    # use a different variable name for clarity where it'll be used only
    # for logging rather than actually accessing/creating files
    log_name = first_filename
    args['log_name'] = first_filename

    f,ax = make_graph_object(**args)

    time_save_start = time.time()

    # saving as .png takes about 130-150 ms
    # saving as .ps or .eps takes about 30-50 ms
    # .svg is about 100 ms - and preserves transparency
    # .pdf is about 80 ms
    # svg and e/ps would have to be rendered before being animated, though
    # possibly making it a moot point
    image_first_filename = first_filename + '.png'
    f.savefig(image_first_filename, bbox_inches='tight', pad_inches=0, 
        dpi=80, transparent=True)

    # if requested, also save with iterative filenames for ease of animation
    if not second_filename == False:
        # copying the file rather than saving again is a lot faster
        shutil.copyfile(image_first_filename, second_filename)

    # close the plot to free the memory. memory is never freed otherwise until
    # script is killed or exits.
    # this line causes a matplotlib backend RuntimeError in a close_event()
    # function ("wrapped C/C++ object of %S has been deleted") in every second
    # iteration, but this appears to be async from main thread and 
    # doesn't appear to influence the correctness of output, 
    # so I'll leave it as is for the time being
    plt.close(f)

    timer.append((log_name + ': make_graph save, ms',
        (time.time()-time_save_start)*1000.0))

    timer.append((log_name + ': make_graph total, ms',
        (time.time()-time_total_start)*1000.0))

def make_accessibility_graph(data, city, first_filename, turn, distance, \
    second_filename = False, show_move_lines = True, show_speeds = False, \
    symbol = '.', time_offset = 0, **extra_args):

    args = locals()

    global timer

    time_total_start = time.time()

    # use a different variable name for clarity where it'll be used only
    # for logging rather than actually accessing/creating files
    log_name = first_filename
    args['log_name'] = first_filename

    time_data_read_start = time.time()

    # TODO: strictly speaking the iteration over data is copied and duplicated 
    # from make_graph_object(). The perf penalty is unlikely to be large, but
    # maintenance might be a pain should I want to change it in 
    # make_graph_object(). So try to reorganize code to fix any duplications.

    max_length = len(data)
    car_count = 0
    latitudes = np.empty(max_length)
    longitudes = np.empty(max_length)

    for car in data:
        if data[car]['seen'] == turn or data[car]['just_moved']:
            if is_latlng_in_bounds(city, data[car]['coords']):
                latitudes[car_count] = data[car]['coords'][0]
                longitudes[car_count] = data[car]['coords'][1]

                car_count += 1

    latitudes = np.round(map_latitude(city, latitudes[:car_count]))
    longitudes = np.round(map_longitude(city, longitudes[:car_count]))

    timer.append((log_name + ': make_accessibility_graph data read, ms',
        (time.time()-time_data_read_start)*1000.0))

    # The below is based off http://stackoverflow.com/questions/8647024/how-to-apply-a-disc-shaped-mask-to-a-numpy-array
    # Basically, we build a True/False mask (master_mask) the same size 
    # as the map. Each 'pixel' within the mask indicates whether the point 
    # is within provided distance from a car.
    # To build this, iterate over all cars and apply a circular mask of Trues
    # (circle_mask) around the point indicating each car. We'll need to shift 
    # things around near the borders of the map, but this is relatively
    # straighforward.

    time_preprocess_start = time.time()

    accessible_colour = (255, 255, 255, 0) # white, fully transparent
    accessible_multiplier = (1, 1, 1, 0.6)
    # if using accessible_multiplier, 160 alpha for inaccessible looks better
    inaccessible_colour = (239, 239, 239, 100) # #efefef, mostly transparent

    # generate basic background, for now uniformly indicating no cars available
    markers = np.empty(
        (MAP_SIZES[city]['MAP_Y'], MAP_SIZES[city]['MAP_X'], 4),
        dtype = np.uint8)
    markers[:] = inaccessible_colour # can't use fill since it isn't a scalar

    # find distance radius, in pixels
    # take mean of latitude- and longitude-based numbers, 
    # which is not quite correct but more than close enough
    lat = MAP_LIMITS[city]['NORTH'] - MAP_LIMITS[city]['SOUTH']
    lat_in_m = lat * DEGREE_LENGTHS[city]['LENGTH_OF_LATITUDE']
    pixel_in_lat_m = lat_in_m / MAP_SIZES[city]['MAP_Y']

    lng = MAP_LIMITS[city]['EAST'] - MAP_LIMITS[city]['WEST']
    lng_in_m = lng * DEGREE_LENGTHS[city]['LENGTH_OF_LONGITUDE']
    pixel_in_lng_m = lng_in_m / MAP_SIZES[city]['MAP_X']

    pixel_in_m = (pixel_in_lat_m + pixel_in_lng_m) / 2 
    radius = np.round(distance / pixel_in_m)

    # generate master availability mask
    master_mask = np.empty(
        (MAP_SIZES[city]['MAP_Y'], MAP_SIZES[city]['MAP_X']),
        dtype = np.bool)
    master_mask.fill(False)
    m_m_shape = master_mask.shape

    # generate basic circle mask
    y,x = np.ogrid[-radius: radius+1, -radius: radius+1]
    circle_mask = x**2+y**2 <= radius**2
    c_m_shape = circle_mask.shape

    timer.append((log_name + ': make_accessibility_graph masks preprocess, ms',
        (time.time()-time_preprocess_start)*1000.0))

    time_iter_start = time.time()

    for i in range(len(latitudes)):
        # to just crudely mark a square area around lat/lng:
        # markers[ (lat - radius) : (lat+radius), (lng-radius) : (lng+radius)] = accessible_colour

        # mask is drawn from top-left corner. to center mask around the point:
        x = latitudes[i] - radius
        y = longitudes[i] - radius

        # find various relevant locations within the matrix...

        # cannot give a negative number as first param in slice
        master_x_start = max(x, 0)
        master_y_start = max(y, 0)
        # but going over boundaries is ok, will trim automatically
        master_x_end = x + c_m_shape[0]
        master_y_end = y + c_m_shape[1]

        circle_x_start = 0
        circle_y_start = 0
        circle_x_end = c_m_shape[0]
        circle_y_end = c_m_shape[1]

        if x < 0:   # trim off left side
            circle_x_start = x * -1
        if y < 0:   # trim off top
            circle_y_start = y * -1
        if master_x_end > m_m_shape[0]: # trim off right side
            circle_x_end = (m_m_shape[0] - master_x_end)
        if master_y_end > m_m_shape[1]: # trim off bottom
            circle_y_end = (m_m_shape[1] - master_y_end)

        # make sure to OR the masks so that earlier circles' Trues 
        # aren't overwritten by later circles' Falses
        master_mask[
            master_x_start : master_x_end, 
            master_y_start : master_y_end
            ] |= circle_mask[
                circle_x_start : circle_x_end, 
                circle_y_start : circle_y_end]

        #markers[master_mask] *= accessible_multiplier
        #master_mask.fill(False)

        #end for

    timer.append((log_name + ': make_accessibility_graph mask iter, ms',
        (time.time()-time_iter_start)*1000.0))

    time_mask_apply_start = time.time()

    # note: can also do something like this: markers[mask] *= (1, 1, 1, 0.5)
    # and it updates everything - should be useful for relative values.
    # except it has to happen within the iteration as shown above, and is also
    # pretty slow. like, adds 1.2 seconds per image slow. see if I can 
    # optimize it somehow, but multiplying a million-item array, even masked,
    # by a vector 200 times might just be inherently a bit slow :(

    markers[master_mask] = accessible_colour

    timer.append((log_name + ': make_accessibility_graph mask apply, ms',
        (time.time()-time_mask_apply_start)*1000.0))

    time_bg_render_start = time.time()

    args['background'] = Image.fromarray(markers, 'RGBA')

    timer.append((log_name + ': make_accessibility_graph bg render, ms',
        (time.time()-time_bg_render_start)*1000.0))

    make_graph(**args)

    timer.append((log_name + ': make_accessibility_graph total, ms',
        (time.time()-time_total_start)*1000.0))

def trace_vehicle(data, provided_vin):
    def format_trip(trip):
        result  = 'start: %s at %f,%f' % \
            (trip['starting_time'], trip['from'][0], trip['from'][1])
        result += ', end: %s at %f,%f' % \
            (trip['ending_time'], trip['to'][0], trip['to'][1])
        result += '\n\tduration: %d minutes' % (trip['duration'] / 60)
        result += '\tdistance: %0.2f km' % (trip['distance'])
        result += '\tfuel: starting %d%%, ending %d%%' % \
            (trip['starting_fuel'], trip['ending_fuel'])

        if trip['ending_fuel'] > trip['starting_fuel']:
            result += ' - refueled'

        return result

    vin = provided_vin
    lines = []

    if vin == 'random':
        vin = choice(list(data.keys()))
    elif vin == 'most_trips':
        # pick the vehicle with most trips. in case of tie, pick first one
        vin = max(data, key = lambda v: len(data[v]['trips']))
        lines.append('vehicle with most trips is %s with %d trips' % \
            (vin, len(data[vin]['trips'])))
    elif vin == 'most_distance':
        vin = max(data, 
            key = lambda v: sum(t['distance'] for t in data[v]['trips']))
        lines.append(
            'vehicle with highest distance travelled is %s with %0.3f km' % \
            (vin, sum(t['distance'] for t in data[vin]['trips'])))
    elif vin == 'most_duration':
        vin = max(data, 
            key = lambda v: sum(t['duration'] for t in data[v]['trips']))
        duration = sum(t['duration'] for t in data[vin]['trips'])/60
        lines.append('vehicle with highest trip duration is %s ' \
            'with %d minutes (%0.2f hours)' % (vin, duration, duration/60))
    elif len(vin) != 17:
        # try to treat as license plate, and find the VIN of the vehicle
        # with such a plate
        vin = vin.replace(' ', '')

        for vehicle in data:
            if data[vehicle]['name'].replace(' ', '') == vin:
                vin = vehicle
                break

    if not vin in data:
        return 'vehicle not found in dataset: %s' % provided_vin

    trips = data[vin]['trips']
    lines.append('trips for vehicle %s: (count %d)' % (vin, len(trips)))
    for trip in trips:
        lines.append(format_trip(trip))

    return '\n'.join(lines)

def print_stats(saved_data, starting_time, t, time_step,
    weird_trip_distance_cutoff = 0.05, weird_trip_time_cutoff = 5,
    # time cutoff should be 2 for 1 minute step data
    weird_trip_fuel_cutoff = 1):
    def trip_breakdown(trips, sorting_bins = [120, 300, 600],
        sorting_lambda = False, label = False):
        # uses stats['total_trips'] defined before calling this subfunction
        lines = []
        for i in sorting_bins:
            if not sorting_lambda:
                trip_count = sum(1 for x in trips if x > i)
            else:
                trip_count = sum(1 for x in trips if sorting_lambda(x, i))

            trip_percent = trip_count * 1.0 / stats['total_trips']

            if not label:
                line = 'trips over %d hours: %s' % \
                    (i/60, trip_count_stats(trip_count))
            else:
                line = label(i, trip_count_stats(trip_count))
            lines.append(line)
        return '\n'.join(lines)

    def trip_count_stats(trip_count):
        # uses time_days and stats['total_trips'] defined 
        # before calling this subfunction

        if abs(time_days-1.0) < 0.01:
            # don't calculate trips per day if value is within 1% of a day
            # that's close enough that the differences won't matter in practice
            return '%d (%0.4f of all trips)' % \
                (trip_count, trip_count * 1.0 / stats['total_trips'])
        else:
            return '%d (%0.2f per day; %0.4f of all trips)' % \
                (trip_count, trip_count/time_days, 
                trip_count * 1.0 / stats['total_trips'])

    def quartiles(data):
        result = {}
        for i in range(5):
            pass
            #result[(i*25)] = sps.scoreatpercentile(data, i*25)
        return result

    def format_quartiles(data, format = '%0.3f'):
        result = ''
        data = quartiles(data)
        for percent in data:
            result += '\t%d\t' % percent
            result += format % data[percent]
            result += '\n'
        return result

    def round_to(value, round_to):
        return round_to*int(value*(1.0/round_to))

    stats = {'total_vehicles': 0,
        'total_trips': 0, 'trips': [],
        'total_distance': 0, 'distances': [], 'distance_bins': [],
        'total_duration': 0, 'durations': [], 'duration_bins': []}
    weird = []
    suspected_round_trip = []
    refueled = []
    for vin in saved_data:
        stats['total_vehicles'] += 1

        trips = 0
        if 'trips' in saved_data[vin]:
            trips = len(saved_data[vin]['trips'])

            for trip in saved_data[vin]['trips']:
                    
                if trip['distance'] <= weird_trip_distance_cutoff:
                    suspected_round_trip.append(trip)
                    test_duration = weird_trip_time_cutoff * 60 # min  to sec
                    print trip
                    if trip['duration'] <= test_duration and \
                        trip['fuel_use'] <= weird_trip_fuel_cutoff:
                        # do not count this trip... it's an anomaly
                        print 'weird'
                        weird.append(trip)
                        trips -= 1
                        continue

                stats['total_trips'] += 1

                stats['total_duration'] += trip['duration']/60
                stats['durations'].append(trip['duration']/60)

                # bin to nearest five minutes (if it isn't already)
                stats['duration_bins'].append(round_to(trip['duration']/60, 5))

                stats['total_distance'] += trip['distance']
                stats['distances'].append(trip['distance'])

                # bin to nearest 0.5 km
                stats['distance_bins'].append(round_to(trip['distance'], 0.5))


                if 'starting_fuel' in trip:
                    if trip['ending_fuel'] > trip['starting_fuel']:
                        refueled.append(trip)

        stats['trips'].append(trips)

    # subtracting time_step below to get last file actually processed
    time_elapsed = t - timedelta(0, time_step*60) - starting_time
    time_days = time_elapsed.total_seconds() / (24*60*60)
    print 'time elapsed: %s (%0.3f days)' % (time_elapsed, time_days)

    print '\ntotal trips: %d (%0.2f per day), total vehicles: %d' % \
        (stats['total_trips'], stats['total_trips'] * 1.0 / time_days,
        stats['total_vehicles'])
    print 'mean total vehicle utilization (%% of day spent moving): %0.3f' % \
        (stats['total_duration'] / stats['total_vehicles'] / (24*60*time_days))

    trip_counter = Counter(stats['trips'])
    sys.stdout.write('\nmean trips per car: %0.2f' % np.mean(stats['trips']))
    if abs(time_days-1.0) > 0.01:
        print ' (%0.2f per day),' % (np.mean(stats['trips']) / time_days),
    else:
        print ',',
    print 'stdev: %0.3f' % np.std(stats['trips'])
    print 'most common trip counts: %s' % trip_counter.most_common(10)
    print 'cars with zero trips: %d' % trip_counter[0]
    print 'trip count per day quartiles:'
    print format_quartiles(np.array(stats['trips'])/time_days, format='%0.2f')

    print 'mean distance per trip (km): %0.2f, stdev: %0.3f' % \
        (np.mean(stats['distances']), np.std(stats['distances']))
    print 'most common distances, rounded to nearest 0.5 km: %s' % \
        Counter(stats['distance_bins']).most_common(10)
    print trip_breakdown(stats['distances'], sorting_bins = [5, 10],
        label = lambda dist, count: 'trips over %d km: %s' % (dist, count))
    print 'distance quartiles: '
    print format_quartiles(stats['distances'])

    print 'mean duration per trip (minutes): %0.2f, stdev: %0.3f' % \
        (np.mean(stats['durations']), np.std(stats['durations']))
    print 'most common durations, rounded to nearest 5 minutes: %s' % \
        Counter(stats['duration_bins']).most_common(10)
    print trip_breakdown(stats['durations'])
    print 'duration quartiles: '
    print format_quartiles(stats['durations'], format = '%d')

    # this is a weirdness with the datasets: 
    # some have lots of short (<50 m, even <10m) trips.
    # e.g., the austin sxsw has about 90 trips per day like that.
    # unfortunately the API doesn't give us mileage, so hard to tell if
    # it was a round trip, or if a car even moved at all.
    # not sure what to do with them yet...
    #weird_backup = weird
    #weird = suspected_round_trip
    durations = list(x['duration']/60 for x in weird)
    distances = list(x['distance'] for x in weird)
    distance_bins = list(int(1000*round_to(x['distance'], 0.005)) 
        for x in weird)
    fuel_uses = list(x['starting_fuel'] - x['ending_fuel'] for x in weird)

    print '\ntrips reported shorter than %d m: %s' % \
        (weird_trip_distance_cutoff * 1000, trip_count_stats(len(weird)))
    print '\ndurations (minutes): mean %0.2f, stdev %0.3f, max %d' % \
        (np.mean(durations), np.std(durations), max(durations))
    print 'most common durations: %s' %Counter(durations).most_common(10)
    print trip_breakdown(durations)
    print '\ndistances (km): mean %0.4f, stdev %0.4f, max %0.2f' % \
        (np.mean(distances), np.std(distances), max(distances))
    print 'most common distances in metres, rounded to nearest 5 m: %s' % \
        Counter(distance_bins).most_common(10)
    print '\nfuel use (in percent capacity): mean %0.2f, stdev %0.3f, max %d' % \
        (np.mean(fuel_uses), np.std(fuel_uses), max(fuel_uses))
    print 'most common fuel uses: %s' % Counter(fuel_uses).most_common(10)
    print trip_breakdown(fuel_uses, sorting_bins = [1, 5, 0],
        sorting_lambda = (lambda x, i: (x > i) if i > 0 else (x < i)),
        label = (lambda fuel, string: 
            'more than %d pp fuel use: %s' % (fuel, string) if (fuel > 0) else
            'refueled: %s' % string))

def batch_process(city, starting_time, dry = False, make_iterations = True, \
    show_move_lines = True, max_files = False, max_skip = 0, file_dir = '', \
    time_step = cars.DATA_COLLECTION_INTERVAL_MINUTES, \
    show_speeds = False, symbol = '.', buses = False, hold_for = 0, \
    distance = False, time_offset = 0, web = False, stats = False, \
    trace = False, \
    **extra_args):

    args = locals()

    global timer, DEBUG

    def get_filepath(city, t, file_dir):
        filename = cars.filename_format % (city, t.year, t.month, t.day, t.hour, t.minute)

        return os.path.join(file_dir, filename)

    def load_file(filepath):
        if not os.path.exists(filepath):
            return False

        f = open(filepath, 'r')
        json_text = f.read()
        f.close()

        try:
            return json.loads(json_text)
        except:
            return False

    i = 1
    t = starting_time
    filepath = get_filepath(city, starting_time, file_dir)

    animation_files_filename = datetime.now().strftime('%Y%m%d-%H%M') + \
        '-' + os.path.basename(filepath)
    animation_files_prefix = os.path.join(os.path.dirname(filepath), 
        animation_files_filename)

    saved_data = {}

    iter_filenames = []

    json_data = load_file(filepath)

    # loop as long as new files exist
    # if we have a limit specified, loop only until limit is reached
    while json_data != False and (max_files is False or i <= max_files):
        time_process_start = time.time()

        print t,

        if 'placemarks' in json_data:
            json_data = json_data['placemarks']

        saved_data,moved_cars = process_data(json_data, t, saved_data,
            **args)
        print 'total known: %d' % len(saved_data),
        print 'moved: %02d' % len(moved_cars)

        timer.append((filepath + ': process_data, ms',
             (time.time()-time_process_start)*1000.0))

        if not dry:
        
            second_filename = False
            if make_iterations:
                second_filename = animation_files_prefix + '_' + \
                    str(i).rjust(3, '0') + '.png'
                iter_filenames.append(second_filename)

            time_graph_start = time.time()

            #make_csv(saved_data, city, filepath, t)

            if distance is False:
                make_graph(data = saved_data, first_filename = filepath, 
                    turn = t, second_filename = second_filename, **args)
            else:
                make_accessibility_graph(data = saved_data,
                    first_filename = filepath, turn = t,
                    second_filename = second_filename, **args)

            timer.append((filepath + ': make_graph or _accessiblity_graph, ms',
                (time.time()-time_graph_start)*1000.0))

        timer.append((filepath + ': total, ms',
            (time.time()-time_process_start)*1000.0))

        # find next file according to provided time_stemp (or default,
        # which is the cars.DATA_COLLECTION_INTERVAL_MINUTES const)
        i = i + 1
        t = t + timedelta(0, time_step*60)
        filepath = get_filepath(city, t, file_dir)

        json_data = load_file(filepath)

        if json_data == False:
            print 'would stop at %s' % filepath

        skipped = 0
        next_t = t
        while json_data == False and skipped < max_skip:
            # this will detect and attempt to counteract missing or malformed 
            # data files, unless instructed otherwise by max_skip = 0
            skipped += 1

            next_t = next_t + timedelta(0, time_step*60)
            next_filepath = get_filepath(city, next_t, file_dir)
            next_json_data = load_file(next_filepath)

            print 'trying %s...' % next_filepath ,

            if next_json_data != False:
                print 'exists, using it instead' ,
                shutil.copy2(next_filepath, filepath)
                json_data = load_file(filepath)

            print

        if DEBUG:
            print '\n'.join(l[0] + ': ' + str(l[1]) for l in timer)

        # reset timer to only keep information about one file at a time
        timer = []

    # print animation information if applicable
    if make_iterations and not dry:
        if web:
            crush_commands = []

            crushed_dir = animation_files_prefix + '-crushed'
            if not os.path.exists(crushed_dir):
                os.makedirs(crushed_dir)

            for filename in iter_filenames:
                crush_commands.append('pngcrush %s %s' % (filename, 
                    os.path.join(crushed_dir, os.path.basename(filename))))

            crush_filebasename = animation_files_prefix
            f = open(crush_filebasename + '-pngcrush', 'w')
            print >> f, '\n'.join(crush_commands)
            os.chmod(crush_filebasename + '-pngcrush', 
                stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR)
            f.close()

            f = open(crush_filebasename + '-filenames', 'w')
            print >> f, json.dumps(iter_filenames)
            f.close()

            print '\nto pngcrush:'
            print './%s-pngcrush' % crush_filebasename

        background_path = os.path.relpath(os.path.join(cars.root_dir,
            'backgrounds/', '%s-background.png' % city))
        png_filepaths = animation_files_prefix + '_%03d.png'
        mp4_path = animation_files_prefix + '.mp4'

        framerate = 8
        frames = i-1
        if time_step < 5:
            framerate = 30
            # for framerates over 25, avconv assumes conversion from 25 fps
            frames = (frames/25)*30

        print '\nto animate:'
        print '''avconv -loop 1 -r %d -i %s -vf 'movie=%s [over], [in][over] overlay' -b 15360000 -frames %d %s''' % (framerate, background_path, png_filepaths, frames, mp4_path)
        # if i wanted to invoke this, just do os.system('avconv...')

    if trace:
        print
        print trace_vehicle(saved_data, trace)

    if stats:
        print
        print_stats(saved_data, starting_time, t, time_step)

    print

def process_commandline():
    global DEBUG

    parser = argparse.ArgumentParser()
    parser.add_argument('starting_filename', type=str,
        help='name of first file to process')
    parser.add_argument('-dry', action='store_true',
        help='dry run: do not generate any images')
    parser.add_argument('-s', '--stats', action='store_true',
        help='generate and print some basic statistics about car2go use')
    parser.add_argument('-t', '--trace', type=str, default=False,
        help='print out all trips of a vehicle found in the dataset; \
            accepts license plates, VINs, \
            "random", "most_trips", "most_distance", and "most_duration"')
    parser.add_argument('-tz', '--time-offset', type=int, default=0,
        help='offset times shown on graphs by TIME_OFFSET hours')
    parser.add_argument('-d', '--distance', type=float, default=False,
        help='mark distance of DISTANCE meters from nearest car on map')
    parser.add_argument('-noiter', '--no-iter', action='store_true', 
        help='do not create consecutively-named files for animating')
    parser.add_argument('-web', action='store_true',
        help='create pngcrush script and JS filelist for HTML animation \
            page use; forces NO_ITER to false')
    parser.add_argument('-nolines', '--no-lines', action='store_true',
        help='do not show lines indicating vehicles\' moves')
    parser.add_argument('-max', '--max-files', type=int, default=False,
        help='limit maximum amount of files to process')
    parser.add_argument('-skip', '--max-skip', type=int, default=3,
        help='amount of missing or malformed sequential data files to try to \
            work around (default 3; specify 0 to work only on data provided)')
    parser.add_argument('-step', '--time-step', type=int,
        default=cars.DATA_COLLECTION_INTERVAL_MINUTES,
        help='analyze data for every TIME_STEP minutes (default %i)' %
            cars.DATA_COLLECTION_INTERVAL_MINUTES)
    parser.add_argument('-speeds', '--show_speeds', action='store_true', 
        help='indicate vehicles\' speeds in addition to locations') 
    parser.add_argument('-hold', '--hold-for', type=int, default=0,
        help='keep drawn points on the map for HOLD_FOR rounds after \
            they would have disappeared')
    parser.add_argument('-symbol', type=str, default='.',
        help='matplotlib symbol to indicate vehicles on the graph \
            (default \'.\', larger \'o\')')
    parser.add_argument('-buses', action='store_true', 
        help='presets for graphing Translink bus movements, \
            equivalent to -speeds -hold=3 -symbol o')
    parser.add_argument('-debug', action='store_true',
        help='print extra debug and timing messages')

    args = parser.parse_args()
    params = vars(args)

    DEBUG = args.debug
    filename = args.starting_filename

    city,starting_time = filename.rsplit('_', 1)

    # strip off directory, if any.
    file_dir,city = os.path.split(city.lower())

    if not os.path.exists(filename):
        if os.path.exists(os.path.join(cars.data_dir, filename)):
            # try to use 'data/' directory automatically, if suitable
            file_dir = cars.data_dir
        else:
            # otherwise we can't find that file
            print 'file not found: ' + filename
            return

    if not city in KNOWN_CITIES:
        print 'unsupported city: ' + city
        return

    try:
        # parse out starting time
        starting_time = datetime.strptime(starting_time, '%Y-%m-%d--%H-%M')
    except:
        print 'time format not recognized: ' + filename
        return

    params['starting_time'] = starting_time
    params['make_iterations'] = not args.no_iter
    params['show_move_lines'] = not args.no_lines

    params['city'] = city
    params['file_dir'] = file_dir

    if args.buses is True:
        params['symbol'] = 'o'
        params['hold_for'] = 3
        params['show_speeds'] = True

    if args.web is True:
        params['make_iterations'] = True

    batch_process(**params)


if __name__ == '__main__':
    process_commandline()

