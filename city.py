#!/usr/bin/env python2
# coding=utf-8

import json
import cars


API_AREAS_URL = 'https://www.car2go.com/api/v2.1/operationareas?loc={loc}&oauth_consumer_key={key}&format=json'

def get_operation_areas(city):
    data_text = cars.get_URL(API_AREAS_URL.format(loc = city, key = cars.OAUTH_KEY))

    return json.loads(data_text).get('placemarks')

def get_lat_long_extent(city):
    areas = get_operation_areas(city)

    latitudes = []
    longitudes = []

    # collect lats and longs across all 'operation areas'
    for area in areas:
        coords = area['coordinates']
        for i in range(0, len(coords), 3):
            latitudes.append(coords[i])
            longitudes.append(coords[i+1])
            # coords[i+2] is always 0 - elevation placeholder?

    # return max/mins for all operation areas
    return max(latitudes), min(latitudes), max(longitudes), min(longitudes)

