#!/usr/bin/env python2
# coding=utf-8


def fill_in_information(system, all_cities):
    for city_key, city_data in all_cities.items():
        city_data['system'] = system
        city_data['name'] = city_key

        if 'display' not in city_data:
            city_data['display'] = city_key.title()

        if 'electric' not in city_data:
            city_data['electric'] = False

        if 'of_interest' not in city_data:
            city_data['of_interest'] = False

        if 'number_first_address' not in city_data:
            city_data['number_first_address'] = False

        if 'MAP_SIZES' not in city_data and 'MAP_LIMITS' in city_data:
            city_data['MAP_SIZES'] = {'MAP_X': 1920, 'MAP_Y': 1080}

        if 'API_AVAILABLE_VEHICLES_HEADERS' not in city_data:
            city_data['API_AVAILABLE_VEHICLES_HEADERS'] = False

    return all_cities


def is_latlng_in_bounds(city_data, lat, lng=False):
    if not lng:
        lng = lat[1]
        lat = lat[0]

    is_lat = city_data['BOUNDS']['SOUTH'] <= lat <= city_data['BOUNDS']['NORTH']
    is_lng = city_data['BOUNDS']['WEST'] <= lng <= city_data['BOUNDS']['EAST']

    return is_lat and is_lng


def get_pixel_size(city_data):
    # find the length in metres represented by one pixel on graph in both lat and lng direction

    lat_range = city_data['MAP_LIMITS']['NORTH'] - city_data['MAP_LIMITS']['SOUTH']
    lat_in_m = lat_range * city_data['DEGREE_LENGTHS']['LENGTH_OF_LATITUDE']
    pixel_in_lat_m = lat_in_m / city_data['MAP_SIZES']['MAP_Y']

    lng_range = city_data['MAP_LIMITS']['EAST'] - city_data['MAP_LIMITS']['WEST']
    lng_in_m = lng_range * city_data['DEGREE_LENGTHS']['LENGTH_OF_LONGITUDE']
    pixel_in_lng_m = lng_in_m / city_data['MAP_SIZES']['MAP_X']

    return pixel_in_lat_m, pixel_in_lng_m


def get_mean_pixel_size(city_data):
    # find the length in metres represented by one pixel on graph

    # take mean of latitude- and longitude-based numbers, 
    # which is not quite correct but more than close enough for most uses

    pixel_in_m = get_pixel_size(city_data)

    return (pixel_in_m[0] + pixel_in_m[1]) / 2 

