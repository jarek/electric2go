#!/usr/bin/env python2
# coding=utf-8

from __future__ import print_function
import os
import stat
import argparse
import shutil
import simplejson as json
from collections import defaultdict
from datetime import datetime, timedelta
from random import choice
import time

import cars
from analysis import stats as process_stats, graph as process_graph, dump as process_dump


timer = []
DEBUG = False


def get_filepath(city, t, file_dir):
    filename = cars.filename_format % (city, t.year, t.month, t.day, t.hour, t.minute)

    return os.path.join(file_dir, filename)


def process_data(system, data_time, prev_data_time, new_availability_json, unfinished_trips, unfinished_parkings):
    # get functions for the correct system
    parse_module = cars.get_carshare_system_module(system_name=system, module_name='parse')
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

    def process_car(car):
        new_car_data = extract_car_data(car)  # get full car info
        result = {'vin': new_car_data['vin'],
                  'coords': (new_car_data['lat'], new_car_data['lng']),
                  'fuel': new_car_data['fuel']}

        for key in OTHER_KEYS:
            result[key] = new_car_data[key]

        return result

    def start_parking(curr_time, new_car_data):
        # car properties will not change during a parking period, so we don't need to save any
        # starting/ending pairs except for starting_time and ending_time
        result = new_car_data

        # save starting time
        result['starting_time'] = curr_time

        return result

    def end_parking(prev_time, unfinished_parking):
        result = unfinished_parking

        # save duration
        result['ending_time'] = prev_time
        result['duration'] = (result['ending_time'] - result['starting_time']).total_seconds()

        return result

    def start_trip(curr_time, starting_car_info):
        result = starting_car_info

        result['from'] = starting_car_info['coords']
        del result['coords']
        result['starting_time'] = curr_time
        result['starting_fuel'] = result['fuel']
        del result['fuel']

        return result

    def end_trip(prev_time, new_car_data, unfinished_trip):
        current_trip_distance = cars.dist(new_car_data['coords'], unfinished_trip['from'])
        current_trip_duration = (prev_time - unfinished_trip['starting_time']).total_seconds()

        trip_data = unfinished_trip
        trip_data['to'] = new_car_data['coords']
        trip_data['ending_time'] = prev_time
        trip_data['distance'] = current_trip_distance
        trip_data['duration'] = current_trip_duration
        if current_trip_duration > 0:
            trip_data['speed'] = current_trip_distance / (current_trip_duration / 3600.0)
        trip_data['ending_fuel'] = new_car_data['fuel']
        trip_data['fuel_use'] = unfinished_trip['starting_fuel'] - new_car_data['fuel']

        trip_data['start'] = {}
        trip_data['end'] = {}
        for key in OTHER_KEYS:
            trip_data['start'][key] = unfinished_trip[key]
            trip_data['end'][key] = new_car_data[key]

        return trip_data

    def end_unstarted_trip(prev_time, new_car_data):
        result = new_car_data

        result['vin'] = new_car_data['vin']
        result['to'] = new_car_data['coords']
        result['ending_time'] = prev_time
        result['ending_fuel'] = new_car_data['fuel']

        result['end'] = {}
        for key in OTHER_KEYS:
            result['end'][key] = new_car_data[key]

        return result

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

            car_data = process_car(car)

            unstarted_potential_trips[vin] = end_unstarted_trip(data_time, car_data)

            unfinished_parkings[vin] = start_parking(data_time, car_data)

        if vin in unfinished_trips:
            # trip has just finished

            car_data = process_car(car)

            finished_trips[vin] = end_trip(data_time, car_data, unfinished_trips[vin])
            del unfinished_trips[vin]

            # TODO: try to filter lapsed reservations - 30 minutes exactly is now the most common trip duration when binned to closest 5 minutes
            # - check directly - and try to guess if it's a lapsed reservation (fuel use? but check 29, 31 minute trips to
            # see if their fuel use isn't usually 0 either)

            unfinished_parkings[vin] = start_parking(data_time, car_data)

        # NOTE: the below condition is valid and is not related to the bug above
        elif vin in unfinished_parkings and (lat != unfinished_parkings[vin]['coords'][0] or lng != unfinished_parkings[vin]['coords'][1]):
            # car has moved but the "trip" took exactly 1 cycle. consequently unfinished_trips and finished_parkings
            # were never created in vins_that_just_became_unavailable loop. need to handle this manually

            # end previous parking and start trip
            finished_parkings[vin] = end_parking(prev_data_time, unfinished_parkings[vin])
            trip_data = start_trip(prev_data_time, finished_parkings[vin])

            # end trip right away and start 'new' parking period in new position
            car_data = process_car(car)
            finished_trips[vin] = end_trip(data_time, car_data, trip_data)
            unfinished_parkings[vin] = start_parking(data_time, car_data)

    vins_that_just_became_unavailable = set(unfinished_parkings.keys()) - available_vins
    for vin in vins_that_just_became_unavailable:
        # trip has just started

        finished_parkings[vin] = end_parking(prev_data_time, unfinished_parkings[vin])
        del unfinished_parkings[vin]

        unfinished_trips[vin] = start_trip(prev_data_time, finished_parkings[vin])

    return finished_trips, finished_parkings, unfinished_trips, unfinished_parkings, unstarted_potential_trips


def batch_load_data(system, city, file_dir, starting_time, time_step, max_files, max_skip):
    global timer, DEBUG

    def load_file(filepath_to_load):
        try:
            with open(filepath_to_load, 'r') as f:
                result = json.load(f)
            return result
        except:
            # return False if file does not exist or is malformed
            return False

    i = 1
    t = starting_time
    prev_t = t
    filepath = get_filepath(city, starting_time, file_dir)

    data_frames = []
    all_trips = []
    all_positions = []
    trips_by_vin = {}

    unfinished_trips = {}
    unfinished_parkings = {}

    finished_trips = defaultdict(list)
    finished_parkings = defaultdict(list)

    unstarted_potential_trips = {}

    missing_files = []

    json_data = load_file(filepath)
    # loop as long as new files exist
    # if we have a limit specified, loop only until limit is reached
    while json_data != False and (max_files is False or i <= max_files):
        time_process_start = time.time()

        print(t, end=' ')

        new_finished_trips, new_finished_parkings, unfinished_trips, unfinished_parkings, unstarted_potential_trips =\
            process_data(system, t, prev_t, json_data, unfinished_trips, unfinished_parkings)

        for vin in new_finished_parkings:
            finished_parkings[vin].append(new_finished_parkings[vin])

        for vin in new_finished_trips:
            finished_trips[vin].append(new_finished_trips[vin])

        timer.append((filepath + ': batch_load_data process_data, ms',
             (time.time()-time_process_start)*1000.0))

        time_organize_start = time.time()

        current_positions = [unfinished_parkings[vin]['coords'] for vin in unfinished_parkings]
        current_positions = [{'coords': p, 'metadata': {}} for p in current_positions]
        all_positions.extend(current_positions)
        current_trips = []
        for vin in new_finished_trips:
            if vin not in trips_by_vin:
                trips_by_vin[vin] = []

            trips_by_vin[vin].append(new_finished_trips[vin])
            all_trips.append(new_finished_trips[vin])
            current_trips.append(new_finished_trips[vin])

        data_frames.append((t, filepath, current_positions, current_trips))

        print('total known: %d' % (len(unfinished_parkings) + len(unfinished_trips)), end=' ')
        print('moved: %02d' % len(new_finished_trips))

        timer.append((filepath + ': batch_load_data organize data, ms',
             (time.time()-time_organize_start)*1000.0))

        # find next file according to provided time_step (or default,
        # which is the cars.DATA_COLLECTION_INTERVAL_MINUTES const)
        i = i + 1
        prev_t = t
        t = t + timedelta(0, time_step*60)
        filepath = get_filepath(city, t, file_dir)

        time_load_start = time.time()

        json_data = load_file(filepath)

        timer.append((filepath + ': batch_load_data load_file, ms',
             (time.time()-time_load_start)*1000.0))

        if json_data == False:
            print('would stop at %s' % filepath)

        skipped = 0
        next_t = t
        while json_data == False and skipped < max_skip:
            # this will detect and attempt to counteract missing or malformed
            # data files, unless instructed otherwise by max_skip = 0
            skipped += 1

            next_t = next_t + timedelta(0, time_step*60)
            next_filepath = get_filepath(city, next_t, file_dir)
            next_json_data = load_file(next_filepath)

            print('trying %s...' % next_filepath, end=' ')

            if next_json_data != False:
                print('exists, using it instead', end=' ')
                missing_files.append(filepath)
                shutil.copy2(next_filepath, filepath)
                json_data = load_file(filepath)

            print()

        timer.append((filepath + ': batch_load_data total load loop, ms',
             (time.time()-time_process_start)*1000.0))

        if DEBUG:
            print('\n'.join(l[0] + ': ' + str(l[1]) for l in timer))

        # reset timer to only keep information about one file at a time
        timer = []

    ending_time = data_frames[-1][0]  # complements starting_time from function params

    result = {
        'finished_trips': finished_trips,
        'finished_parkings': finished_parkings,
        'unfinished_trips': unfinished_trips,
        'unfinished_parkings': unfinished_parkings,
        'unstarted_trips': unstarted_potential_trips,
        'metadata': {
            'starting_time': starting_time,
            'ending_time': ending_time,
            'time_step': time_step,
            'missing': missing_files
        }
    }

    def json_serializer(obj):
        # default doesn't serialize dates... tell it to use isoformat()
        # syntax from http://blog.codevariety.com/2012/01/06/python-serializing-dates-datetime-datetime-into-json/
        # TODO: might also want to update a worse solution to same problem in analysis/dump.py
        return obj.isoformat() if hasattr(obj, 'isoformat') else obj

    with open(datetime.now().strftime('%Y%m%d-%H%M%S') + '-alldata.json', 'w') as f:
        json.dump(result, f, default=json_serializer, indent=2)

    # TODO: also return unstarted_potential_trips
    return data_frames, all_positions, all_trips, trips_by_vin, ending_time, i

def filter_trips_list(all_trips_by_vin, find_by):
    """
    Used for filtering that can only be done once the complete list is found,
    e.g. picking a car with most trips or most duration.
    :return: a trips list for the requested car
    """

    vin = find_by  # allow finding by passing in VIN verbatim

    if find_by == 'random':
        vin = choice(list(all_trips_by_vin.keys()))
    elif find_by == 'most_trips':
        # pick the vehicle with most trips. in case of tie, pick first one
        vin = max(all_trips_by_vin,
                  key=lambda v: len(all_trips_by_vin[v]))
    elif find_by == 'most_distance':
        vin = max(all_trips_by_vin,
                  key=lambda v: sum(t['distance'] for t in all_trips_by_vin[v]))
    elif find_by == 'most_duration':
        vin = max(all_trips_by_vin,
                  key=lambda v: sum(t['duration'] for t in all_trips_by_vin[v]))

    if vin not in all_trips_by_vin:
        raise KeyError("VIN %s not found in all_trips_by_vin" % vin)

    return all_trips_by_vin[vin]

def batch_process(system, city, starting_time, dry = False, make_iterations = True,
    show_move_lines = True, max_files = False, max_skip = 0, file_dir = '',
    time_step = cars.DATA_COLLECTION_INTERVAL_MINUTES,
    show_speeds = False, symbol = '.',
    distance = False, tz_offset = 0, web = False, stats = False,
    filter_trips = False, trace = False, dump_trips = False,
    all_positions_image = False, all_trips_lines_image = False,
    all_trips_points_image = False,
    **extra_args):

    global timer, DEBUG

    # read in all data
    time_load_start = time.time()
    (data_frames, all_positions, all_trips,
     trips_by_vin, ending_time, total_frames) = batch_load_data(system, city, file_dir,
                                                                starting_time, time_step,
                                                                max_files, max_skip)
    if DEBUG:
        time_load_total = (time.time() - time_load_start)
        time_load_frame = time_load_total / total_frames
        print('\ntotal data load loop: {:d} frames, {:f} s, {:f} ms per frame, {:f} s per 60 frames, {:f} s per 1440 frames'.format(
            total_frames, time_load_total, time_load_frame * 1000, time_load_frame * 60, time_load_frame * 1440))

    # set up params for iteratively-named images
    starting_file_name = get_filepath(city, starting_time, file_dir)
    animation_files_filename = datetime.now().strftime('%Y%m%d-%H%M') + \
        '-' + os.path.basename(starting_file_name)
    animation_files_prefix = os.path.join(os.path.dirname(starting_file_name),
        animation_files_filename)
    iter_filenames = []

    # generate images
    if not dry:
        for index, data in enumerate(data_frames):
            # reset timer to only keep information about one file at a time
            timer = []
            process_graph.timer = []

            turn, filepath, current_positions, current_trips = data

            if not show_move_lines:
                current_trips = []

            image_filename = filepath + '.png'
            copy_filename = False
            if make_iterations:
                copy_filename = animation_files_prefix + '_' + \
                    str(index).rjust(3, '0') + '.png'
                iter_filenames.append(copy_filename)

            time_graph_start = time.time()

            process_graph.make_graph(system, city, current_positions, current_trips,
                                     image_filename, copy_filename, turn,
                                     show_speeds, distance, symbol, tz_offset)

            time_graph = (time.time() - time_graph_start) * 1000.0
            timer.append((filepath + ': make_graph, ms', time_graph))

            print(turn, 'generated graph in %d ms' % time_graph)

            if DEBUG:
                print('\n'.join(l[0] + ': ' + str(l[1]) for l in process_graph.timer))
                print('\n'.join(l[0] + ': ' + str(l[1]) for l in timer))

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
            print('\n'.join(crush_commands), file=f)
            os.chmod(crush_filebasename + '-pngcrush', 
                stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR)
            f.close()

            f = open(crush_filebasename + '-filenames', 'w')
            print(json.dumps(iter_filenames), file=f)
            f.close()

            print('\nto pngcrush:')
            print('./%s-pngcrush' % crush_filebasename)

        background_path = os.path.relpath(os.path.join(cars.root_dir,
            'backgrounds/', '%s-background.png' % city))
        png_filepaths = animation_files_prefix + '_%03d.png'
        mp4_path = animation_files_prefix + '.mp4'

        framerate = 30
        # to my best understanding, my "input" is the static background image
        # which avconv assumes to be "25 fps".
        # to get output at 30 fps to be correct length to include all frames,
        # I need to convert framecount from 25 fps to 30 fps
        frames = ((total_frames - 1)/25)*framerate

        print('\nto animate:')
        print('''avconv -loop 1 -r %d -i %s -vf 'movie=%s [over], [in][over] overlay' -b 15360000 -frames %d %s''' % (framerate, background_path, png_filepaths, frames, mp4_path))
        # if i wanted to invoke this, just do os.system('avconv...')

    # TODO: allow filtering the data (both trips and positions) by timeframe, latlng, etc

    if filter_trips:
        all_trips = filter_trips_list(trips_by_vin, filter_trips)

    if dump_trips:
        filename = dump_trips
        process_dump.dump_trips(all_trips, filename, tz_offset)

    if trace and filter_trips:
        process_stats.trace_vehicle(all_trips, filter_trips)

    if stats:
        process_stats.stats(all_trips, trips_by_vin.keys(), starting_time, ending_time)

    if all_positions_image:
        process_graph.make_positions_graph(system, city, all_positions, all_positions_image, symbol)

    if all_trips_lines_image:
        process_graph.make_trips_graph(system, city, all_trips, all_trips_lines_image)

    if all_trips_points_image:
        process_graph.make_trip_origin_destination_graph(system, city, all_trips, all_trips_points_image, symbol)

    if DEBUG:
        print('\n'.join(l[0] + ': ' + str(l[1]) for l in process_graph.timer))
        print('\n'.join(l[0] + ': ' + str(l[1]) for l in timer))

    print()

def process_commandline():
    global DEBUG

    parser = argparse.ArgumentParser()
    parser.add_argument('-debug', action='store_true',
        help='print extra debug and timing messages')
    parser.add_argument('system', type=str,
        help='system to be used (e.g. car2go, drivenow, ...)')
    parser.add_argument('starting_filename', type=str,
        help='name of first file to process')
    parser.add_argument('-max', '--max-files', type=int, default=False,
        help='limit maximum amount of files to process')
    parser.add_argument('-skip', '--max-skip', type=int, default=3,
        help='amount of missing or malformed sequential data files to try to \
            work around (default 3; specify 0 to work only on data provided)')
    parser.add_argument('-step', '--time-step', type=int,
        default=cars.DATA_COLLECTION_INTERVAL_MINUTES,
        help='analyze data for every TIME_STEP minutes (default %i)' %
            cars.DATA_COLLECTION_INTERVAL_MINUTES)
    parser.add_argument('-tz', '--tz-offset', type=int, default=0,
        help='offset times by TZ_OFFSET hours')
    parser.add_argument('-dry', action='store_true',
        help='dry run: do not generate any images')
    parser.add_argument('-noiter', '--no-iter', action='store_true',
        help='do not create consecutively-named files for animating')
    parser.add_argument('-web', action='store_true',
        help='create pngcrush script and JS filelist for HTML animation \
            page use; forces NO_ITER to false')
    parser.add_argument('-nolines', '--no-lines', action='store_true',
        help='do not show lines indicating vehicles\' moves')
    parser.add_argument('-d', '--distance', type=float, default=False,
        help='mark distance of DISTANCE meters from nearest car on map')
    parser.add_argument('-speeds', '--show_speeds', action='store_true',
        help='indicate vehicles\' speeds in addition to locations')
    parser.add_argument('-symbol', type=str, default='.',
        help='matplotlib symbol to indicate vehicles on the graph \
            (default \'.\', larger \'o\')')
    parser.add_argument('-f', '--filter_trips', type=str, default=False,
        help='filter list of all trips by vehicle; \
            accepts license plates, VINs, "random", "most_trips", "most_distance", and "most_duration". \
            affects output of STATS, TRACE, DUMP_TRIPS, and ALL_*_IMAGE params')
    parser.add_argument('-s', '--stats', action='store_true',
        help='generate and print some basic statistics about carshare use')
    parser.add_argument('-t', '--trace', action='store_true',
        help='print out all trips of a vehicle found in the dataset; \
            requires that FILTER_TRIPS is set')
    parser.add_argument('-dt', '--dump-trips', type=str, default=False,
        help='dump JSON of all trips to filename passed as param')
    parser.add_argument('-ap', '--all-positions-image', type=str, default=False,
        help='create image of all vehicle positions in the dataset \
            and save to ALL_POSITIONS_IMAGE')
    parser.add_argument('-atl', '--all-trips-lines-image', type=str, default=False,
        help='create image of all trips in the dataset and save to ALL_TRIPS_LINES_IMAGE')
    parser.add_argument('-atp', '--all-trips-points-image', type=str, default=False,
        help='create image of all trips in the dataset and save to ALL_TRIPS_POINTS_IMAGE')

    args = parser.parse_args()
    params = vars(args)

    DEBUG = args.debug
    filename = args.starting_filename

    city,starting_time = filename.rsplit('_', 1)

    # strip off directory, if any.
    file_dir,city = os.path.split(city.lower())

    if not os.path.exists(filename):
        print('file not found: ' + filename)
        return

    cities_for_system = cars.get_all_cities(args.system)
    if not city in cities_for_system:
        print('unsupported city {city_name} for system {system_name}'.format(city_name=city, system_name=args.system))
        return

    try:
        # parse out starting time
        starting_time = datetime.strptime(starting_time, '%Y-%m-%d--%H-%M')
    except:
        print('time format not recognized: ' + filename)
        return

    params['starting_time'] = starting_time
    params['make_iterations'] = not args.no_iter
    params['show_move_lines'] = not args.no_lines

    params['city'] = city
    params['file_dir'] = file_dir

    if args.web is True:
        params['make_iterations'] = True

    batch_process(**params)


if __name__ == '__main__':
    process_commandline()

