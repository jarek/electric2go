# coding=utf-8


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

