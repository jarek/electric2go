# coding=utf-8

from __future__ import print_function
import os
import sys

from . import cmdline, generate
from .. import cars
from . import stats as process_stats, graph as process_graph


def make_graph_from_frame(result_dict, data, animation_files_prefix, symbol,
                          show_move_lines, show_speeds, distance, tz_offset):
    index, turn, current_positions, current_trips = data

    if not show_move_lines:
        current_trips = []

    image_filename = '{file}_{i:05d}.png'.format(file=animation_files_prefix, i=index)

    process_graph.make_graph(result_dict, current_positions, current_trips,
                             image_filename, turn,
                             show_speeds, distance, symbol, tz_offset)

    # TODO: figure out a way to report progress better
    print('{t} generated as {i}'.format(t=turn, i=image_filename), file=sys.stderr)

    return image_filename


def batch_process(video=False, tz_offset=0, stats=False,
                  show_move_lines=True, show_speeds=False, symbol='.', distance=False,
                  all_positions_image=False, all_trips_lines_image=False, all_trips_points_image=False):
    """
    :return: does not return anything
    """

    # read in all data
    result_dict = cmdline.read_json()

    # set up params for iteratively-named images
    city = result_dict['metadata']['city']
    animation_files_prefix = cars.output_file_name(description=city)

    # generate images
    if video:
        # make_graph_from_frame is currently fairly slow (~2 seconds per frame).
        # The map can be fairly easily parallelized, e.g. http://stackoverflow.com/a/5237665/1265923
        # TODO: make sure everything inside has no side effects then parallelize
        iter_filenames = [
            make_graph_from_frame(result_dict, data, animation_files_prefix, symbol,
                                  show_move_lines, show_speeds, distance, tz_offset)
            for data in generate.build_data_frames(result_dict)
        ]
        # TODO: refactor so that there exists a function that returns iter_filenames

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

    if stats:
        written_file = process_stats.stats(result_dict, tz_offset)
        print(written_file)  # provide output name for easier reuse

    if all_positions_image:
        process_graph.make_positions_graph(result_dict, all_positions_image, symbol)

    if all_trips_lines_image:
        process_graph.make_trips_graph(result_dict, all_trips_lines_image)

    if all_trips_points_image:
        process_graph.make_trip_origin_destination_graph(result_dict, all_trips_points_image, symbol)
