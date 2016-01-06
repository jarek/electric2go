# coding=utf-8

from __future__ import print_function
import sys

from . import generate, graph
from ..systems import get_background_as_image


def make_graph_from_frame(result_dict, data, filename_prefix, symbol,
                          show_speeds, distance, tz_offset):
    index, turn, current_positions, current_trips = data

    image_filename = '{file}_{i:05d}.png'.format(file=filename_prefix,
                                                 i=index)

    graph.make_graph(result_dict, current_positions, current_trips, image_filename,
                     turn, show_speeds, distance, symbol, tz_offset)

    # TODO: figure out a way to report progress better
    print('{t} generated as {i}'.format(t=turn, i=image_filename),
          file=sys.stderr)

    return image_filename


def make_animate_command(result_dict, filename_prefix, frame_count):
    background_path = get_background_as_image(result_dict)
    png_filepaths = '{file}_%05d.png'.format(file=filename_prefix)
    mp4_path = '{file}.mp4'.format(file=filename_prefix)

    framerate = 30
    # to my best understanding, my "input" is the static background image
    # which avconv assumes to be "25 fps".
    # to get output at 30 fps to be correct length to include all frames,
    # I need to convert framecount from 25 fps to 30 fps
    frames = (frame_count / 25.0) * framerate

    command_template = "avconv -loop 1 -r %d -i %s -vf 'movie=%s [over], [in][over] overlay' -b 15360000 -frames %d %s"
    command = command_template % (framerate, background_path, png_filepaths, frames, mp4_path)

    return command


def make_video_frames(result_dict, filename_prefix, distance, include_trips,
                      show_speeds, symbol, tz_offset):
    # make_graph_from_frame is currently fairly slow (~2 seconds per frame).
    # The map can be fairly easily parallelized, e.g. http://stackoverflow.com/a/5237665/1265923
    # TODO: parallelize
    # It appears graph functions will be safe to parallelize, they
    # all ultimately go to matplotlib which is parallel-safe
    # according to http://stackoverflow.com/a/4662511/1265923
    generated_images = [
        make_graph_from_frame(result_dict, data, filename_prefix, symbol,
                              show_speeds, distance, tz_offset)
        for data in generate.build_data_frames(result_dict, include_trips)
    ]

    animate_command_text = make_animate_command(result_dict, filename_prefix,
                                                len(generated_images))

    return animate_command_text, generated_images
