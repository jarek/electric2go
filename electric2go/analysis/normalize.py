# coding=utf-8

import os
import codecs
from collections import defaultdict
import datetime
import glob
import tarfile
import zipfile

from .cmdline import json  # will be either simplejson or json
from .. import dist, current_git_revision, files, systems


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


def process_data(parser, data_time, prev_data_time, available_cars, result_dict):
    # declare local variable names for easier access
    unfinished_trips = result_dict['unfinished_trips']
    unfinished_parkings = result_dict['unfinished_parkings']
    unstarted_potential_trips = result_dict['unstarted_trips']
    finished_parkings = result_dict['finished_parkings']
    finished_trips = result_dict['finished_trips']
    vehicles = result_dict['vehicles']

    # internal, not returned
    original_car_data = {}

    # called by start_parking and _get_ending_trip_data
    def process_car(car_info):
        p_vin, p_lat, p_lng = parser.get_car_basics(car_info)

        return {
            'vin': p_vin,

            # transitional, TODO: should be merged into changing_properties
            'coords': (p_lat, p_lng),

            'changing_properties': parser.get_car_changing_properties(car_info)
        }

    def start_parking(curr_time, new_car_data):
        data = process_car(new_car_data)

        result = {
            'vin': data['vin'],
            'coords': data['coords'],

            # car properties will not change during a parking period, so we don't need to save any
            # starting/ending pairs except for starting_time and ending_time
            'starting_time': curr_time,

            # store initial version of changing data in to compare against later
            # make it a list so new versions can be appended as needed
            'changing_data': [(curr_time, parser.get_car_parking_drift(car))]
        }

        # save the rest of properties straight in the parking object
        result.update(data['changing_properties'])

        return result

    def end_parking(prev_time, unfinished_parking):
        # this takes in a finished_parking (already processed, so we can't run
        # get_car_changing_properties() on it), because we have no current car
        # info when a trip is starting as the car is missing from the API

        result = dict.copy(unfinished_parking)

        result['ending_time'] = prev_time
        result = calculate_parking(result)

        return result

    def start_trip(curr_time, just_finished_parking):
        # this takes in a finished_parking (already processed, so we can't run
        # get_car_changing_properties() on it), because we have no current car
        # info when a trip is starting as the car is missing from the API.
        # consequently, we take in the data we do have and convert it into
        # trip information.

        result = dict.copy(just_finished_parking)

        # TODO: move it into 'start' dict - needs updates elsewhere
        result['from'] = result['coords']
        del result['coords']

        # TODO: move it into 'start' dict - needs updates elsewhere
        result['starting_fuel'] = result['fuel']
        del result['fuel']

        result['starting_time'] = curr_time
        del result['ending_time']  # that was the ending time of the parking

        # at this point, `result` contains the output of parser.get_car_changing_properties
        # plus the following keys:
        # - from start_parking: vin, coords, starting_time (though overwritten just now), changing_data
        # - from end_parking: ending_time (but deleted just now)
        # - from calculate_parking: duration
        # By excluding those keys, we can get the keys that are changing,
        # and write them into the "start" dictionary.
        keys_to_exclude = {'vin', 'coords', 'starting_time',
                           'duration', 'changing_data'}
        result['start'] = {key: result[key] for key in result
                           if key not in keys_to_exclude}

        return result

    def _get_ending_trip_data(prev_time, ending_car_info):
        data = process_car(ending_car_info)
        new_properties = data['changing_properties']

        trip_data = {
            'vin': data['vin'],
            'ending_time': prev_time,

            'to': data['coords'],
            'ending_fuel': new_properties['fuel'],

            # write all keys in the parser response except for fuel, lat, and lng
            # (which are handled above) into 'end' key
            'end': {key: new_properties[key]
                    for key in new_properties
                    if key not in {'fuel', 'lat', 'lng'}}
        }

        return trip_data

    def end_trip(prev_time, ending_car_info, unfinished_trip):
        # save data at end of trip
        ending_trip_data = _get_ending_trip_data(prev_time, ending_car_info)

        # update with data from the start of the trip
        trip_data = unfinished_trip
        trip_data.update(ending_trip_data)

        # calculate trip distance, duration, etc, based on start and end data
        trip_data = calculate_trip(trip_data)

        return trip_data

    def end_unstarted_trip(prev_time, ending_car_info):
        # essentially the same as end_trip except all bits that depend on
        # unfinished_trip have been removed - we can only return the end info

        return _get_ending_trip_data(prev_time, ending_car_info)

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

        vin, lat, lng = parser.get_car_basics(car)
        available_vins.add(vin)

        # most of the time, none of these conditionals will be processed - most cars park for much more than one cycle

        if vin not in unfinished_parkings and vin not in unfinished_trips:
            # returning from an unknown trip, the first time we're seeing the car

            # save original raw info
            original_car_data[vin] = car

            unstarted_potential_trips[vin] = end_unstarted_trip(data_time, car)

            unfinished_parkings[vin] = start_parking(data_time, car)

        if vin in unfinished_trips:
            # trip has just finished

            finished_trips[vin].append(end_trip(data_time, car, unfinished_trips[vin]))
            del unfinished_trips[vin]

            unfinished_parkings[vin] = start_parking(data_time, car)

        elif vin in unfinished_parkings and (lat != unfinished_parkings[vin]['coords'][0] or lng != unfinished_parkings[vin]['coords'][1]):
            # car has moved but the "trip" took exactly 1 cycle. consequently unfinished_trips and finished_parkings
            # were never created in vins_that_just_became_unavailable loop. need to handle this manually

            # end previous parking and start trip
            finished_parking = end_parking(prev_data_time, unfinished_parkings[vin])
            finished_parkings[vin].append(finished_parking)
            started_trip = start_trip(prev_data_time, finished_parking)

            # end trip right away and start 'new' parking period in new position
            finished_trips[vin].append(end_trip(data_time, car, started_trip))
            unfinished_parkings[vin] = start_parking(data_time, car)

        else:
            # if we're here, we have an unfinished parking.
            # test one more thing: if a car is parked and charging at the same time,
            # its properties can change during the parking period.
            # compare current data with last-stored data for the parking.
            current_data = parser.get_car_parking_drift(car)

            # note, 'changing_data' is guaranteed to have at least one item
            # because that's added in start_parking()
            (previous_data_timestamp, previous_data) = unfinished_parkings[vin]['changing_data'][-1]

            if previous_data != current_data:
                unfinished_parkings[vin]['changing_data'].append(
                    # TODO: should this be data_time or prev_data_time? note also same thing in start_parking
                    # and corresponding comparison to `turn` in generate.roll_out_changing_data
                    # Think about it a bit and see what makes more sense.
                    (prev_data_time, current_data)
                )

    new_vins = available_vins - set(vehicles.keys())
    for vin in new_vins:
        # save info about a car that doesn't change over time
        # (e.g. car model), we will only hit this once per car per dataset

        vehicles[vin] = parser.get_car_unchanging_properties(original_car_data[vin])

    vins_that_just_became_unavailable = set(unfinished_parkings.keys()) - available_vins
    for vin in vins_that_just_became_unavailable:
        # trip has just started

        finished_parking = end_parking(prev_data_time, unfinished_parkings[vin])
        finished_parkings[vin].append(finished_parking)
        del unfinished_parkings[vin]

        unfinished_trips[vin] = start_trip(prev_data_time, finished_parking)

    return result_dict


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

        elif os.path.isfile(filename) and zipfile.is_zipfile(filename):
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
        parser = systems.get_parser(system)
    except ImportError:
        msg = 'Unrecognized system "{sys}" (unable to import "{sys}.parse")'
        raise ValueError(msg.format(sys=system))

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

    # Set up the result_dict which will be built up then returned
    result_dict = {
        # These two dicts contain ongoing record of things that are happening.
        # The dicts are modified in each iteration as cars' trips and parkings
        # end or start.
        'unfinished_trips': {},
        'unfinished_parkings': {},

        # These are built up as we iterate, and only appended to.
        'finished_trips': defaultdict(list),
        'finished_parkings': defaultdict(list),
        'unstarted_trips': {},  # a car can have only one unstarted trip -
                                # so we don't need a list here

        # Stores information about cars which we expect to not change
        # during the duration of the dataset. This can be stuff like
        # car model or automatic/manual transmission.
        # Note: Unexpected things will happen if a property changes during
        # the dataset duration. However, it will still be better than
        # throwing out this data altogether, which we were doing previously.
        'vehicles': defaultdict(dict),

        # Keeps additional system info, outside the vehicles information.
        # This is stuff like system maps and city properties.
        # I expect this not to change within a day.
        'system': {},

        # Metadata about the dataset
        'metadata': {
            'electric2go_revision': current_git_revision(),
            'processing_started': datetime.datetime.utcnow(),

            'system': system,
            'city': city,
            'starting_time': starting_time,
            'time_step': time_step,
            'missing': []  # appended to as we load data
            # 'ending_time' will be added once all data is loaded
        }
    }

    # With the first data point, make sure it's valid format for the system,
    # then extract and save data other than available cars.
    # See comment for result_dict['system'] definition above.
    # Do not increment t so that same datapoint will be read again in the loop
    first_data = data_archive.load_data_point(t)
    first_available_cars = parser.get_cars(first_data)
    if not first_available_cars:
        raise ValueError('First file found is invalid or contains no cars.'
                         'Provide starting_time for first valid dataset.')
    result_dict['system'] = parser.get_everything_except_cars(first_data)

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
            # handle outer JSON structure and get a list we can loop through
            available_cars = parser.get_cars(data)

            result_dict = process_data(parser, t, prev_t,
                                       available_cars, result_dict)

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
            result_dict['metadata']['missing'].append(t)

        # get next data time according to provided time_step
        t += datetime.timedelta(seconds=time_step)

    data_archive.close()

    # Save the actual ending time of the resulting dataset,
    # that is, the last valid data point found and analyzed.
    # Not necessarily the same as input ending_time - files could have ran out
    # before we got to input ending_time, or the last file could have been
    # malformed.
    result_dict['metadata']['ending_time'] = prev_t

    return result_dict
