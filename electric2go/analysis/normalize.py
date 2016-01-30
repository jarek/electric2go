# coding=utf-8

import os
import sys
import codecs
from collections import defaultdict
import datetime
import glob
import tarfile
import zipfile

from .cmdline import json  # will be either simplejson or json
from .. import dist, files, systems


def calculate_parking(data):
    data['duration'] = (data['ending_time'] - data['starting_time']).total_seconds()

    return data


def calculate_trip(trip_data):
    """
    Calculates a trip's distance, duration, speed, and fuel use.
    """

    current_trip_distance = dist(trip_data['to'], trip_data['from'])
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


class Electric2goDataArchive():
    last_file_time = None

    load_data_point = None  # will be dynamically assigned

    handle_to_close = None  # will be assigned if we need to close something at the end

    def __init__(self, city, filename):
        if os.path.isfile(filename) and tarfile.is_tarfile(filename):
            # Handle being provided a tar file.

            self.load_data_point = self.tar_loader

            # Performance comments:
            # The most efficient we can get is to scan the whole list of files
            # in the archive once. After that, we can get file handles
            # by providing a TarInfo object, which has the needed
            # offset information.
            # We can get TarInfos with getmembers(), which does the whole-file
            # scan. We then associate TarInfos with their data timestamp,
            # as we ultimately fetch the data with the timestamp.

            self.tarfile = tarfile.open(filename)
            self.handle_to_close = self.tarfile

            # tarfile.getmembers() is in same order as files in the tarfile
            all_files_tarinfos = self.tarfile.getmembers()

            # Get time of first and last data point.
            # This implementation assumes that files in the tarfile
            # are in alphabetical/chronological order. This assumption
            # holds for my data scripts
            first_file = all_files_tarinfos[0].name
            self.first_file_time = files.get_time_from_filename(first_file)

            last_file = all_files_tarinfos[-1].name
            self.last_file_time = files.get_time_from_filename(last_file)

            # dict mapping datetimes to tarinfos
            self.tarinfos = {files.get_time_from_filename(t.name): t
                             for t in all_files_tarinfos}

        elif os.path.isfile(filename) and filename.endswith('.zip'):
            # see comments for tarfile logic above, the logic here is the same
            # only translated to zipfile module's idioms

            self.load_data_point = self.zip_loader

            # Performance comments:
            # If provided a filename in the constructor, ZipFile module will
            # open the archive separately each time we request a file inside.
            # If provided a file handle, it will use it. Do that to avoid
            # reopening the archive 1440 times for a day's data.
            # zipfile.infolist() returns a list that was created when
            # the archive was opened. Calling it repeatedly has no penalty,
            # but it will be easier to call it once and construct the dict
            # mapping times to filenames during initialization here.

            self.handle_to_close = open(filename, 'rb')
            self.zipfile = zipfile.ZipFile(self.handle_to_close, 'r')

            all_files_zipinfos = self.zipfile.infolist()

            first_file = all_files_zipinfos[0].filename
            self.first_file_time = files.get_time_from_filename(first_file)

            last_file = all_files_zipinfos[-1].filename
            self.last_file_time = files.get_time_from_filename(last_file)

            self.zipinfos = {files.get_time_from_filename(z.filename): z
                             for z in all_files_zipinfos}

        else:
            # Handle files in a directory, not zipped or tarred.

            self.city = city
            self.directory = os.path.split(filename.lower())[0]

            self.load_data_point = self.file_loader

            # Get time of first and last data point.
            # First search for all files matching naming scheme
            # for the current city, then find the min/max file, then its date.
            # This implementation requires that data files are named in
            # alphabetical-chronological order - it seems unusual and wrong
            # to do it any other way, so hopefully it won't be a problem.
            # There doesn't seem to be an easier/faster way to do this as
            # Python's directory lists all return in arbitrary order.

            mask = files.FILENAME_MASK.format(city=self.city)
            matching_files = glob.glob(os.path.join(self.directory, mask))
            sorted_files = sorted(matching_files)

            first_file = sorted_files[0]
            self.first_file_time = files.get_time_from_filename(first_file)

            last_file = sorted_files[-1]
            self.last_file_time = files.get_time_from_filename(last_file)

    def close(self):
        if self.handle_to_close:
            self.handle_to_close.close()

    def file_loader(self, t):
        filename = files.get_file_name(self.city, t)
        filepath_to_load = os.path.join(self.directory, filename)

        try:
            with open(filepath_to_load, 'r') as f:
                result = json.load(f)
            return result
        except (IOError, ValueError):
            # return False if file does not exist or is malformed
            return False

    def tar_loader(self, t):
        if t in self.tarinfos:
            # tarfile.extractfile() doesn't support context managers
            # on Python 2 :(

            f = self.tarfile.extractfile(self.tarinfos[t])

            reader = codecs.getreader('utf-8')

            try:
                result = json.load(reader(f))
            except ValueError:
                # return False if file is not valid JSON
                result = False

            f.close()

            return result
        else:
            # return False if file is not in the archive
            return False

    def zip_loader(self, t):
        if t in self.zipinfos:
            with self.zipfile.open(self.zipinfos[t]) as f:
                reader = codecs.getreader('utf-8')

                try:
                    result = json.load(reader(f))
                except ValueError:
                    # return False if file is not valid JSON
                    result = False

            return result
        else:
            # return False if file is not in the archive
            return False


def batch_load_data(system, starting_filename, starting_time, ending_time, time_step):
    # get parser functions for the correct system
    try:
        parse_module = systems.get_parser(system)
    except ImportError:
        sys.exit('unsupported system {system_name}'.format(system_name=system))

    # get city name. split if we were provided a path including directory
    file_name = os.path.split(starting_filename)[1]
    city = files.get_city_from_filename(file_name)

    # if we were provided with a file, not an archive, get its starting time
    try:
        starting_file_time = files.get_time_from_filename(file_name)
    except ValueError:
        # for archives, use low value so it is not chosen in max() below
        starting_file_time = datetime.datetime(year=1, month=1, day=1)

    data_archive = Electric2goDataArchive(city, starting_filename)

    if not starting_time:
        # If starting_time is provided, use it.
        # If it is not provided, use the later of:
        # 1) starting time parsed from starting_filename, if that was a file
        # 2) data_archive.first_file_time
        starting_time = max(starting_file_time, data_archive.first_file_time)

    if (not ending_time) or ending_time > data_archive.last_file_time:
        # If ending_time not provided, scan until we get to the last file.
        # If provided, check if it is earlier than data actually available;
        # if not, only use what is available.
        ending_time = data_archive.last_file_time

    # `t` will be the time of the current iteration. Start from the start.
    t = starting_time

    # prev_t will be the time of the previous *good* dataset.
    # In the very first iteration of main loop, value of prev_t is not used.
    # This initial value will be only used when there is no data at all,
    # in which case it'll become the ending_time. We want ending_time
    # to be at least somewhat useful, so assign t.
    prev_t = t

    # These two dicts contain ongoing record of things that are happening.
    # The dicts are modified in each iteration as cars' trips and parkings
    # end or start.
    unfinished_trips = {}
    unfinished_parkings = {}

    # These are built up as we iterate, and only appended to.
    unstarted_trips = {}
    finished_trips = defaultdict(list)
    finished_parkings = defaultdict(list)
    missing_data_points = []

    # Loop until we get to end of dataset or until the limit requested.
    while t <= ending_time:
        # get current time's data
        data = data_archive.load_data_point(t)

        # It seems very tempting to turn data_archive / Electric2goDataArchive
        # into an iterator and just call next() rather than incrementing
        # a timestamp here. However, we need the timestamp for
        # missing_data_points list, so we'd have to have the iterator return
        # the timestamp as well. At that point we might as well keep track
        # of time in this loop.

        if data:
            new_finished_trips, new_finished_parkings, unfinished_trips, unfinished_parkings, unstarted_trips_this_round =\
                process_data(parse_module, t, prev_t, data, unfinished_trips, unfinished_parkings)

            # update data dictionaries
            unstarted_trips.update(unstarted_trips_this_round)
            for vin in new_finished_parkings:
                finished_parkings[vin].append(new_finished_parkings[vin])
            for vin in new_finished_trips:
                finished_trips[vin].append(new_finished_trips[vin])

            # update last valid data timestamp
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

        else:
            # Data file not found or was malformed, report it as missing.
            missing_data_points.append(t)

        # get next data time according to provided time_step
        t += datetime.timedelta(seconds=time_step)

    data_archive.close()

    # actual_ending_time is the actual ending time of the resulting dataset,
    # that is, the last valid data point found and analyzed.
    # Not necessarily the same as input ending_time - files could have ran out
    # before we got to input ending_time, or the last file could have been
    # malformed.
    actual_ending_time = prev_t

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
            'ending_time': actual_ending_time,
            'time_step': time_step,
            'missing': missing_data_points
        }
    }

    return result
