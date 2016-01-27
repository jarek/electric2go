# coding=utf-8

import os
from datetime import datetime


root_dir = os.path.dirname(os.path.realpath(__file__))

FILENAME_FORMAT = '%s_%04d-%02d-%02d--%02d-%02d'
FILENAME_MASK = '{city}_????-??-??--??-??'


def get_data_dir(city_data):
    return os.path.join(root_dir, 'data', city_data['system'])


def get_current_file_path(city_data):
    data_dir = get_data_dir(city_data)
    return os.path.join(data_dir, 'current_%s' % city_data['name'])


def get_file_name(city_name, t):
    # same format as parsed by parse_date()
    return FILENAME_FORMAT % (city_name, t.year, t.month, t.day, t.hour, t.minute)


def get_file_path(city_data, t):
    filename = get_file_name(city_data['name'], t)
    return os.path.join(get_data_dir(city_data), filename)


def get_city_and_time_from_filename(filename):
    # Slice off the city name by finding last underscore in the filename.
    # This must match FILENAME_FORMAT / FILENAME_MASK.
    city, leftover = filename.rsplit('_', 1)

    # Find full extension by splitting on first dot in the leftover part.
    # Don't use splitext as it gives us ".gz" as the extension
    # for "wien_2015-06-19.tar.gz".
    # That can be one of the correct interpretations, but we can't use it,
    # we need the extension to be ".tar.gz".
    # Note that since we need only the bit before the dot, file_parts[0]
    # nicely handles the case where the is no extension.
    file_parts = leftover.split('.', 1)
    file_time_string = file_parts[0]

    # Finally, add 00:00 for files with extensions, if not already there.
    # Extension-less files should always have the time part already there.
    if len(file_parts) == 2 and not file_time_string.endswith('--00-00'):
        file_time_string += '--00-00'

    file_time = parse_date(file_time_string)

    return city, file_time


def get_time_from_filename(filename):
    return get_city_and_time_from_filename(filename)[1]


def parse_date(string):
    # same format as produced by get_file_name() from FILENAME_FORMAT
    return datetime.strptime(string, '%Y-%m-%d--%H-%M')
