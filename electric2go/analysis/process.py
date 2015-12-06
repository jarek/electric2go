# coding=utf-8

from __future__ import print_function
import os
import sys
import stat
import json
from datetime import timedelta
import time

from . import cmdline
from .. import cars
from . import stats as process_stats, graph as process_graph


def build_data_frames(result_dict):
    # temp function to facilitate switchover and testing to new data format

    # shorter variable names for easier access
    turn = result_dict['metadata']['starting_time']
    fin_parkings = result_dict['finished_parkings']
    fin_trips = result_dict['finished_trips']
    unfinished_parkings = result_dict['unfinished_parkings']

    # flatten lists
    finished_parkings = [item for vin in fin_parkings for item in fin_parkings[vin]]
    finished_trips = [trip for vin in fin_trips for trip in fin_trips[vin]]

    index = 0

    while turn <= result_dict['metadata']['ending_time']:
        # The condition of `p['starting_time'] <= turn <= p['ending_time']`
        # (with the two less-than-or-equal) in the statement to get
        # current_positions is correct.

        # I was initially afraid it was wrong because parking periods
        # are defined in process_data as follows:
        #   "A parking period starts on data_time and ends on prev_data_time."
        # and so I thought this had to be `turn < p['ending_time']`

        # But actually the equals on both ends is fine. process_data does the
        # logical filtering as to when a parking starts and ends. With this,
        # in process_data output, cars are still available when
        # `turn == p['ending_time']`. Trying to do `turn < p['ending_time']`
        # would be double-filtering.
        # (Confirmed with actually looking at source data.)

        current_positions = [p for p in finished_parkings
                             if p['starting_time'] <= turn <= p['ending_time']]
        current_positions.extend([unfinished_parkings[vin] for vin in unfinished_parkings
                                  if unfinished_parkings[vin]['starting_time'] <= turn])

        current_trips = [p for p in finished_trips
                         if p['ending_time'] == turn]

        data_frame = (index, turn, current_positions, current_trips)
        yield data_frame

        index += 1
        turn += timedelta(seconds=result_dict['metadata']['time_step'])


def make_graph_from_frame(system, city, data, animation_files_prefix, symbol,
                          show_move_lines, show_speeds, distance, tz_offset, debug):
    # TODO: migrate away from using the global timer objects
    # and printing timer messages directly
    # It appears process_graph functions will be safe to parallelize, they
    # all ultimately go to matplotlib which is parallel-safe
    # according to http://stackoverflow.com/a/4662511/1265923

    # reset timer to only keep information about one file at a time
    timer = []
    process_graph.timer = []

    index, turn, current_positions, current_trips = data

    if not show_move_lines:
        current_trips = []

    image_filename = '{file}_{i:05d}.png'.format(file=animation_files_prefix, i=index)

    time_graph_start = time.time()

    process_graph.make_graph(system, city, current_positions, current_trips,
                             image_filename, turn,
                             show_speeds, distance, symbol, tz_offset)

    time_graph = (time.time() - time_graph_start) * 1000.0
    timer.append((str(turn) + ': make_graph, ms', time_graph))

    print(turn, 'generated graph in %d ms' % time_graph, file=sys.stderr)

    if debug:
        print('\n'.join(l[0] + ': ' + str(l[1]) for l in process_graph.timer), file=sys.stderr)
        print('\n'.join(l[0] + ': ' + str(l[1]) for l in timer), file=sys.stderr)

    return image_filename


def batch_process(video=False, web=False, tz_offset=0, stats=False,
                  show_move_lines=True, show_speeds=False, symbol='.', distance=False,
                  all_positions_image=False, all_trips_lines_image=False, all_trips_points_image=False,
                  debug=False):
    """
    :return: does not return anything
    """

    timer = []

    # read in all data
    time_load_start = time.time()

    result_dict = cmdline.read_json()

    system = result_dict['metadata']['system']
    city = result_dict['metadata']['city']

    if debug:
        time_load_total = (time.time() - time_load_start)
        data_duration = (result_dict['metadata']['ending_time'] - result_dict['metadata']['starting_time']).total_seconds()
        time_load_minute = time_load_total / (data_duration/60)
        print('\ntotal data load loop: {:f} hours of data, {:f} s, {:f} ms per 1 minute of data, {:f} s per 1 day of data'.format(
            data_duration/3600, time_load_total, time_load_minute * 1000, time_load_minute * 1440),
            file=sys.stderr)

    # set up params for iteratively-named images
    animation_files_prefix = cars.output_file_name(description=city)

    # generate images
    if video:
        # make_graph_from_frame is currently fairly slow (~2 seconds per frame).
        # The map can be fairly easily parallelized, e.g. http://stackoverflow.com/a/5237665/1265923
        # TODO: clean up timers/prints in make_graph_from_frame so it can be parallelized safely
        iter_filenames = [
            make_graph_from_frame(system, city, data, animation_files_prefix, symbol,
                                  show_move_lines, show_speeds, distance, tz_offset, debug)
            for data in build_data_frames(result_dict)
        ]

        # print animation information if applicable
        if web:
            filenames_file_name = cars.output_file_name('filenames', 'json')
            with open(filenames_file_name, 'w') as f:
                json.dump(iter_filenames, f)

            crushed_dir = cars.output_file_name('crushed-images')
            if not os.path.exists(crushed_dir):
                os.makedirs(crushed_dir)

            crush_commands = ['pngcrush %s %s' %
                              (filename, os.path.join(crushed_dir, os.path.basename(filename)))
                              for filename in iter_filenames]

            command_file_name = cars.output_file_name('pngcrush')
            with open(command_file_name, 'w') as f:
                f.write('\n'.join(crush_commands))
            os.chmod(command_file_name, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

            print('\nto pngcrush:')
            print('./' + command_file_name)

        background_path = os.path.relpath(os.path.join(cars.root_dir,
            'systems/backgrounds/', '%s-background.png' % city))
        png_filepaths = animation_files_prefix + '_%05d.png'
        mp4_path = animation_files_prefix + '.mp4'

        framerate = 30
        # to my best understanding, my "input" is the static background image
        # which avconv assumes to be "25 fps".
        # to get output at 30 fps to be correct length to include all frames,
        # I need to convert framecount from 25 fps to 30 fps
        frames = (len(iter_filenames)/25.0)*framerate

        print('\nto animate:')
        print('''avconv -loop 1 -r %d -i %s -vf 'movie=%s [over], [in][over] overlay' -b 15360000 -frames %d %s''' % (framerate, background_path, png_filepaths, frames, mp4_path))
        # if i wanted to invoke this, just do os.system('avconv...')

    all_trips = [trip for vin in result_dict['finished_trips'] for trip in result_dict['finished_trips'][vin]]

    if stats:
        written_file = process_stats.stats(result_dict, tz_offset)
        print(written_file)  # provide output name for easier reuse

    if all_positions_image:
        process_graph.make_positions_graph(system, city, result_dict, all_positions_image, symbol)

    if all_trips_lines_image:
        process_graph.make_trips_graph(system, city, all_trips, all_trips_lines_image)

    if all_trips_points_image:
        process_graph.make_trip_origin_destination_graph(system, city, all_trips, all_trips_points_image, symbol)

    if debug:
        print('\n'.join(l[0] + ': ' + str(l[1]) for l in process_graph.timer), file=sys.stderr)
        print('\n'.join(l[0] + ': ' + str(l[1]) for l in timer), file=sys.stderr)
