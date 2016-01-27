# coding=utf-8

from datetime import datetime
from math import radians, sin, cos, asin, sqrt


def output_file_name(description, extension=''):
    file_name = '{date}_{desc}'.format(
        date=datetime.now().strftime('%Y%m%d-%H%M%S'),
        desc=description)

    if extension:
        file_name = '{name}.{ext}'.format(name=file_name, ext=extension)

    return file_name


def dist(ll1, ll2):
    # Haversine formula implementation to get distance between two points
    # adapted from http://www.movable-type.co.uk/scripts/latlong.html
    # see also http://stackoverflow.com/questions/27928/calculate-distance-between-two-ll-points
    # and http://stackoverflow.com/questions/4913349/haversine-formula-in-python

    # the js equivalent of this code is used in sort.js
    # - any changes should be reflected in both

    earth_radius = 6371  # Radius of the earth in km

    lat1, lng1 = ll1
    lat2, lng2 = ll2

    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)

    # Using d_lat = lat2_rad - lat1_rad gives marginally different results,
    # because floating point
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)

    a = sin(d_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(d_lng/2)**2
    c = 2 * asin(sqrt(a))

    return earth_radius * c
