#!/usr/bin/env python3
# coding=utf-8

from __future__ import print_function
import os
import sys
import argparse
import codecs
from collections import defaultdict
from datetime import datetime, timedelta
import time
import tarfile

from cmdline import json  # will be either simplejson or json
import cmdline
import cars


DEBUG = False


def calculate_parking(data):
    data['duration'] = (data['ending_time'] - data['starting_time']).total_seconds()

    return data


def calculate_trip(trip_data):
    """
    Calculates a trip's distance, duration, speed, and fuel use.
    """

    current_trip_distance = cars.dist(trip_data['to'], trip_data['from'])
    current_trip_duration = (trip_data['ending_time'] - trip_data['starting_time']).total_seconds()

    trip_data['distance'] = current_trip_distance
    trip_data['duration'] = current_trip_duration
    if current_trip_duration > 0:
        trip_data['speed'] = current_trip_distance / (current_trip_duration / 3600.0)
    trip_data['fuel_use'] = trip_data['starting_fuel'] - trip_data['ending_fuel']

    return trip_data


def process_data(parse_module, data_time, prev_data_time, new_availability_json, unfinished_trips, unfinished_parkings):
    # get parser functions for the system
    get_cars_from_json = getattr(parse_module, 'get_cars_from_json')
    extract_car_basics = getattr(parse_module, 'extract_car_basics')
    extract_car_data = getattr(parse_module, 'extract_car_data')

    # handle outer JSON structure and get a list we can loop through
    available_cars = get_cars_from_json(new_availability_json)

    # keys that are handled explicitly within the loop
    RECOGNIZED_KEYS = ['vin', 'lat', 'lng', 'fuel']

    # ignored keys that should not be tracked for trips - stuff that won't change during a trip
    IGNORED_KEYS = ['name', 'license_plate', 'address', 'model', 'color', 'fuel_type', 'transmission']

    if len(available_cars):
        # assume all cars will have same key structure (otherwise we'd have merged systems), and look at first one
        OTHER_KEYS = [key for key in extract_car_data(available_cars[0]).keys()
                      if key not in RECOGNIZED_KEYS and key not in IGNORED_KEYS]

    # unfinished_trips and unfinished_parkings come from params, are updated, then returned
    unstarted_potential_trips = {}  # to be returned
    finished_trips = {}  # to be returned
    finished_parkings = {}  # to be returned

    # called by start_parking, end_trip, and end_unstarted_trip
    def process_car(car_info):
        new_car_data = extract_car_data(car_info)  # get full car info
        result = {'vin': new_car_data['vin'],
                  'coords': (new_car_data['lat'], new_car_data['lng']),
                  'fuel': new_car_data['fuel']}

        for key in OTHER_KEYS:
            result[key] = new_car_data[key]

        return result

    def start_parking(curr_time, new_car_data):
        result = process_car(new_car_data)

        # car properties will not change during a parking period, so we don't need to save any
        # starting/ending pairs except for starting_time and ending_time
        result['starting_time'] = curr_time

        return result

    def end_parking(prev_time, unfinished_parking):
        result = dict.copy(unfinished_parking)

        result['ending_time'] = prev_time
        result = calculate_parking(result)

        return result

    def start_trip(curr_time, starting_car_info):
        result = dict.copy(starting_car_info)

        result['from'] = starting_car_info['coords']
        del result['coords']
        result['starting_time'] = curr_time
        del result['ending_time']
        result['starting_fuel'] = result['fuel']
        del result['fuel']

        return result

    def end_trip(prev_time, ending_car_info, unfinished_trip):
        new_car_data = process_car(ending_car_info)

        trip_data = unfinished_trip
        trip_data['to'] = new_car_data['coords']
        trip_data['ending_time'] = prev_time
        trip_data['ending_fuel'] = new_car_data['fuel']

        trip_data = calculate_trip(trip_data)

        trip_data['start'] = {}
        trip_data['end'] = {}
        for key in OTHER_KEYS:
            trip_data['start'][key] = unfinished_trip[key]
            trip_data['end'][key] = new_car_data[key]
            del trip_data[key]

        return trip_data

    def end_unstarted_trip(prev_time, ending_car_info):
        # essentially the same as end_trip except all bits that depend on
        # unfinished_trip have been removed
        trip_data = process_car(ending_car_info)

        trip_data['ending_time'] = prev_time
        trip_data['to'] = trip_data['coords']
        del trip_data['coords']
        trip_data['ending_fuel'] = trip_data['fuel']
        del trip_data['fuel']

        trip_data['end'] = {}
        for key in OTHER_KEYS:
            trip_data['end'][key] = trip_data[key]
            del trip_data[key]

        return trip_data

    """
    Set this up as a defacto state machine with two states.
    A car is either in parking or in motion. These are stored in unfinished_parkings and unfinished_trips respectively.

    Based on a cycle's data:
    - a car might finish a trip: it then is removed from unfinished_trips, is added to unfinished_parkings, and
      added to finished_trips.
    - a car might start a trip: it is then removed from unfinished_parkings, is added to unfinished_trips, and
      added to finished_parkings

    There are some special cases: a 1-cycle-long trip which causes a car to flip out of and back into
    unfinished_parkings, and initialization of a "new" car (treated as finishing an "unstarted" trip, since if it
    wasn't on a trip it would have been in unfinished_parkings before).

    data_time is when we know about a car's position; prev_data_time is the previous cycle.
    A parking period starts on data_time and ends on prev_data_time.
    A trip starts on prev_data_time and ends on data_time.
    """

    available_vins = set()
    for car in available_cars:

        vin, lat, lng = extract_car_basics(car)
        available_vins.add(vin)

        # most of the time, none of these conditionals will be processed - most cars park for much more than one cycle

        if vin not in unfinished_parkings and vin not in unfinished_trips:
            # returning from an unknown trip, the first time we're seeing the car

            unstarted_potential_trips[vin] = end_unstarted_trip(data_time, car)

            unfinished_parkings[vin] = start_parking(data_time, car)

        if vin in unfinished_trips:
            # trip has just finished

            finished_trips[vin] = end_trip(data_time, car, unfinished_trips[vin])
            del unfinished_trips[vin]

            unfinished_parkings[vin] = start_parking(data_time, car)

        elif vin in unfinished_parkings and (lat != unfinished_parkings[vin]['coords'][0] or lng != unfinished_parkings[vin]['coords'][1]):
            # car has moved but the "trip" took exactly 1 cycle. consequently unfinished_trips and finished_parkings
            # were never created in vins_that_just_became_unavailable loop. need to handle this manually

            # end previous parking and start trip
            finished_parkings[vin] = end_parking(prev_data_time, unfinished_parkings[vin])
            trip_data = start_trip(prev_data_time, finished_parkings[vin])

            # end trip right away and start 'new' parking period in new position
            finished_trips[vin] = end_trip(data_time, car, trip_data)
            unfinished_parkings[vin] = start_parking(data_time, car)

    vins_that_just_became_unavailable = set(unfinished_parkings.keys()) - available_vins
    for vin in vins_that_just_became_unavailable:
        # trip has just started

        finished_parkings[vin] = end_parking(prev_data_time, unfinished_parkings[vin])
        del unfinished_parkings[vin]

        unfinished_trips[vin] = start_trip(prev_data_time, finished_parkings[vin])

    return finished_trips, finished_parkings, unfinished_trips, unfinished_parkings, unstarted_potential_trips


def batch_load_data(system, city, location, starting_time, time_step, max_steps, max_skip):
    global DEBUG

    def load_data_from_file(city, t, file_dir):
        filename = cars.get_file_name(city, t)
        filepath_to_load = os.path.join(file_dir, filename)

        try:
            with open(filepath_to_load, 'r') as f:
                result = json.load(f)
            return result
        except (IOError, ValueError):
            # return False if file does not exist or is malformed
            return False

    def load_data_from_tar(city, t, archive):
        filename = cars.get_file_name(city, t)

        try:
            # extractfile doesn't support "with" syntax :(
            f = archive.extractfile(location_prefix + filename)

            try:
                reader = codecs.getreader('utf-8')
                result = json.load(reader(f))
            except ValueError:
                # return False if file is not valid JSON
                result = False

            f.close()

            return result
        except KeyError:
            # return False if file is not in the archive
            return False

    # get parser functions for the correct system
    try:
        parse_module = cars.get_carshare_system_module(system_name=system, module_name='parse')
    except ImportError:
        sys.exit('unsupported system {system_name}'.format(system_name=system))

    # vary function based on file_dir / location. if location is an archive file,
    # preload the archive and have the function read files from there
    location_prefix = ''
    if os.path.isfile(location) and tarfile.is_tarfile(location):
        location = tarfile.open(location)

        # handle file name prefixes like "./vancouver_2015-06-19--00-00"
        first_file = location.next()
        location_prefix = first_file.name.split(city)[0]

        load_data_point = load_data_from_tar
    else:
        load_data_point = load_data_from_file

    timer = []
    time_load_start = time.time()

    # load_next_data increments t before loading in data, so subtract
    # 1 * time_step to get the first data file in first iteration
    t = starting_time - timedelta(minutes=time_step)

    # in the very first iteration, value of prev_t is not used, so use None
    prev_t = None

    skipped = 0
    max_t = starting_time + timedelta(minutes=time_step * (max_steps - 1))

    unfinished_trips = {}
    unfinished_parkings = {}
    unstarted_trips = {}

    finished_trips = defaultdict(list)
    finished_parkings = defaultdict(list)

    missing_data_points = []
    previously_skipped = []

    # Normally, loop as long as new data points exist and we haven't skipped
    # too many bad data points.
    # If we have a limit specified (in max_steps), loop only until limit is reached
    while t < max_t and skipped <= max_skip:
        time_process_start = time.time()

        # get next data point according to provided time_step
        t += timedelta(minutes=time_step)

        data = load_data_point(city, t, location)

        if data:
            new_finished_trips, new_finished_parkings, unfinished_trips, unfinished_parkings, unstarted_trips_this_round =\
                process_data(parse_module, t, prev_t, data, unfinished_trips, unfinished_parkings)

            # update data dictionaries
            unstarted_trips.update(unstarted_trips_this_round)
            for vin in new_finished_parkings:
                finished_parkings[vin].append(new_finished_parkings[vin])
            for vin in new_finished_trips:
                finished_trips[vin].append(new_finished_trips[vin])

            timer.append(('{city} {t}: batch_load_data process_data, ms'.format(city=city, t=t),
                          (time.time()-time_process_start)*1000.0))

            prev_t = t
            """ prev_t is now last data point that was successfully loaded.
            This means that the first good frame after some bad frames
            (that were skipped) will have process_data with t and prev_t
            separated by more than 1 time_step.
            For example, consider the following dataset:
                data
                data <- trip starts
                data
                data
                data
                missing
                missing
                data <- trip seen to end
                data
            We could assume trip took 6 time_steps, or 4 time_steps - either
            is defensible.
            I've decided on interpretation resulting in 6 in the past, so I'll
            stick with that. """

            if skipped > 0:
                # if we got to a good point after skipping some bad points,
                # save data points that we skipped
                missing_data_points.extend(previously_skipped)

                # reset out the counters for possible future skip episodes
                skipped = 0
                previously_skipped = []

        else:
            # data point file was not found or not valid, try to skip past it
            skipped += 1
            previously_skipped.append(t)

            print('file for {city} {t} is missing or malformed'.format(city=city, t=t),
                  file=sys.stderr)

        timer.append(('{city} {t}: batch_load_data total load loop, ms'.format(city=city, t=t),
                      (time.time()-time_process_start)*1000.0))

        if DEBUG:
            print('\n'.join(l[0] + ': ' + str(l[1]) for l in timer), file=sys.stderr)

        # reset timer to only keep information about one data point at a time
        timer = []

    # ending_time is the actual ending time of the resulting dataset,
    # that is, the last valid data point found.
    # Not necessarily the same as max_time - files could have ran out before
    # we got to max_time.
    ending_time = prev_t

    result = {
        'finished_trips': finished_trips,
        'finished_parkings': finished_parkings,
        'unfinished_trips': unfinished_trips,
        'unfinished_parkings': unfinished_parkings,
        'unstarted_trips': unstarted_trips,
        'metadata': {
            'system': system,
            'city': city,
            'starting_time': starting_time,
            'ending_time': ending_time,
            'time_step': time_step*60,
            'missing': missing_data_points
        }
    }

    if DEBUG:
        time_load_total = (time.time() - time_load_start)
        data_duration = (ending_time - starting_time).total_seconds()
        time_load_minute = time_load_total / (data_duration/60)
        print('\ntotal data load loop: {:f} hours of data, {:f} s, {:f} ms per 1 minute of data, {:f} s per 1 day of data'.format(
            data_duration/3600, time_load_total, time_load_minute * 1000, time_load_minute * 1440),
            file=sys.stderr)

    return result


def process_commandline():
    global DEBUG

    parser = argparse.ArgumentParser()
    parser.add_argument('-debug', action='store_true',
                        help='print extra debug and timing messages to stderr')
    parser.add_argument('system', type=str,
                        help='system to be used (e.g. car2go, drivenow, ...)')
    parser.add_argument('starting_filename', type=str,
                        help='name of archive of files or the first file')
    parser.add_argument('-st', '--starting-time', type=str,
                        help='if using an archive, optional first data point '
                             'to process; format YYYY-mm-DD--HH-MM')
    parser.add_argument('-step', '--time-step', type=int, default=1,
                        help='each step is TIME_STEP minutes (default 1)')
    parser.add_argument('-max', '--max-steps', type=int, default=44647,
                        help='limit maximum amount of TIME_STEPs to process '
                             '(default 44647 = 1440 * 31)')
    parser.add_argument('-skip', '--max-skip', type=int, default=3,
                        help='amount of missing or malformed sequential '
                             'steps to try to work around (default 3; '
                             'specify 0 to work only on data provided)')
    parser.add_argument('-i', '--indent', type=int, default=None,
                        help='indent for output JSON (default none)')

    args = parser.parse_args()
    params = vars(args)

    DEBUG = args.debug
    json_indent = args.indent
    filename = args.starting_filename

    if not os.path.exists(filename):
        sys.exit('file not found: ' + filename)

    # Handle the following cases:
    # - filename being like "car2go-archives/wien_2015-06-19.tgz" <- archive
    # - filename being like "car2go-archives/wien_2015-06-19--04-00" <- first of many files

    city, leftover = filename.rsplit('_', 1)

    if not params['starting_time']:
        # don't use splitext so we correctly handle filenames like wien_2015-06-19.tar.gz
        parts = leftover.split('.', 1)

        if len(parts) == 2 and not parts[0].endswith('--00-00'):
            # replace file extension with 00:00 if needed
            leftover = leftover.replace('.' + parts[1], '--00-00')

        params['starting_time'] = leftover

    try:
        # parse out starting time
        params['starting_time'] = datetime.strptime(params['starting_time'],
                                                    '%Y-%m-%d--%H-%M')
    except ValueError:
        sys.exit('time format not recognized: ' + params['starting_time'])

    if tarfile.is_tarfile(filename):
        location = filename
        city = os.path.split(city.lower())[1]
    else:
        location, city = os.path.split(city.lower())

    params['city'] = city
    params['location'] = location

    del params['debug']
    del params['starting_filename']
    del params['indent']

    result = batch_load_data(**params)

    cmdline.write_json(result, indent=json_indent)


if __name__ == '__main__':
    process_commandline()
