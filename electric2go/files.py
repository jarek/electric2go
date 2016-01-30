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


def _split_filename(filename):
    # Slice off the city name by finding last underscore in the filename.
    # This must match FILENAME_FORMAT / FILENAME_MASK.
    return filename.rsplit('_', 1)


def get_city_from_filename(filename):
    return _split_filename(filename)[0]


def get_time_from_filename(filename):
    return parse_date(_split_filename(filename)[1])


def parse_date(string):
    # same format as produced by get_file_name() from FILENAME_FORMAT
    return datetime.strptime(string, '%Y-%m-%d--%H-%M')
