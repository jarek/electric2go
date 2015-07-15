#!/usr/bin/env python2
# coding=utf-8

from __future__ import unicode_literals

from . import API_URL, OAUTH_KEY


# DEGREE_LENGTHs come http://www.csgnetwork.com/degreelenllavcalc.html
# could calculate ourselves but meh. would need city's latitude

# for verification, check that:
# MAP_Y_DIMENSION / MAP_X_DIMENSION / (NORTH-SOUTH)/(EAST-WEST) ~= LENGTH_OF_LATITUDE / LENGTH_OF_LONGITUDE
# e.g. for Portland:
# 1080/1920 / (45.583-45.435)/(122.83514-122.45986) ~= 111141.91 / 78130.36
# 0.5625 / 0.394372202 = 1.426317568 ~= 1.422518852

CITIES = {
    'amsterdam': {'electric': 'all'},
    'austin': {'number_first_address': True,
        'BOUNDS': {
            'NORTH': 30.368, # exact value 30.367937, or 30.400427 incl The Domain
            'SOUTH': 30.212, # exact value 30.212427
            'EAST': -97.672, # exact value -97.672966
            'WEST': -97.804  # exact value -97.803764
        },
        'MAP_LIMITS': {
            # values are different than home area bounds - 16:9 aspect ratio
            # map scale is 1:99776
            'NORTH': 30.368,
            'SOUTH': 30.212,
            'EAST': -97.5774,
            'WEST': -97.8986
        },
        'DEGREE_LENGTHS': {
            # for latitude 30.29
            'LENGTH_OF_LATITUDE': 110857.33,
            'LENGTH_OF_LONGITUDE': 96204.48
        },
        'MAP_SIZES': {
            # 720/1280 / (30.368-30.212)/(97.8986-97.5774) ~= 110857.33 / 96204.48
            # 0.5625 / 0.485678705 = 1.158173077 ~= 1.152309435
            'MAP_X': 1280,
            'MAP_Y': 720
        },
        'LABELS': {
            'fontsizes': [30, 22, 30, 18, 18],
            'lines': [
                (20, 720 - 50),
                (20, 720 - 82),
                (20, 720 - 122),
                (20, 720 - 155),
                (20, 720 - 180)
            ]
        },
    },
    'berlin': {
        'BOUNDS': {
            # rudimentary values for testing is_latlng_in_bounds function
            'NORTH': 53,
            'SOUTH': 52,
            'EAST': 14,
            'WEST': 13
        },
        'MAP_LIMITS': {
            # rudimentary values for testing is_latlng_in_bounds function
            'NORTH': 53,
            'SOUTH': 52,
            'EAST': 14,
            'WEST': 13
        }
    },
    'calgary': {'of_interest': True, 'number_first_address': True,
        'BOUNDS': {
            'NORTH': 51.11526,
            'SOUTH': 50.985497,
            'EAST': -114.0008,
            'WEST': -114.226364
        },
        'MAP_LIMITS': {
            # E&W values are different than home area bounds - 16:9 aspect ratio
            # map scale is 75945 for 1920x1080
            # http://render.openstreetmap.org/cgi-bin/export?bbox=-114.297025989,50.985497,-113.930138011,51.11526&scale=75945&format=png
            'NORTH': 51.11526,
            'SOUTH': 50.985497,
            'EAST': -113.930138011,
            'WEST': -114.297025989
        },
        'DEGREE_LENGTHS': {
            # for latitude 51.05
            'LENGTH_OF_LATITUDE': 111249.20,
            'LENGTH_OF_LONGITUDE': 70122.18
        },
        'MAP_SIZES': {
            'MAP_X': 1920,
            'MAP_Y': 1080
        },
        'LABELS': {
            'fontsizes': [35, 22, 30, 18],
            'lines': [
                (50, 1080 - 465),
                (50, 1080 - 503),
                (50, 1080 - 542),
                (50, 1080 - 580)
            ]
        }
    },
    'columbus': {
        'of_interest': True, 'number_first_address': True,
        'BOUNDS': {
            'NORTH': 40.075535,
            'SOUTH': 39.92898,
            'EAST': -82.91279,
            'WEST': -83.07589
        },
        'MAP_LIMITS': {
            # E&W values are different than home area bounds - 16:9 aspect ratio
            # N&S values are marginally larger to give a small margin at edges of map
            # map scale is 75171 for 1920x1080
            # http://render.openstreetmap.org/cgi-bin/export?bbox=-83.175943115,39.92398,-82.812736885,40.080535&scale=75171&format=png
            'NORTH': 40.080535,
            'SOUTH': 39.92398,
            'EAST': -82.812736885,
            'WEST': -83.175943115
        },
        'DEGREE_LENGTHS': {
            # for latitude 40.00
            'LENGTH_OF_LATITUDE': 111034.61,
            'LENGTH_OF_LONGITUDE': 85393.83
        },
        'MAP_SIZES': {
            'MAP_X': 1920,
            'MAP_Y': 1080
        },
        'LABELS': {
            'fontsizes': [35, 22, 30, 18],
            'lines': [
                (200, 1080 - 55),
                (200, 1080 - 93),
                (200, 1080 - 132),
                (200, 1080 - 170)
            ]
        }
    },
    'columbus_osu': {
        'display': 'OSU area, Columbus',
        'BOUNDS': {
            # this map limits the area to be examined to University District
            # (Lane Avenue / I-670 / Summit St / SR-315)
            # plus whatever fits to east and west to get to 16:9 aspect ratio
            'NORTH': 40.00664,  # Lane Avenue
            'SOUTH': 39.97341,  # I-670
            'EAST': -82.97675,  # original limit would be -82.99971, Summit St
            'WEST': -83.05380   # original limit would be -83.03084, SR-315
        },
        'MAP_LIMITS': {
            # map scale is 23920 for 1280x720
            # http://render.openstreetmap.org/cgi-bin/export?bbox=-83.05380,39.97341,-82.97675,40.00664&scale=23920&format=png
            # map scale is 15952 for 1920x1080
            # http://render.openstreetmap.org/cgi-bin/export?bbox=-83.05380,39.97341,-82.97675,40.00664&scale=15952&format=png
            'NORTH': 40.00664,
            'SOUTH': 39.97341,
            'EAST': -82.97675,
            'WEST': -83.05380
        },
        'DEGREE_LENGTHS': {
            # for latitude 40.00, close enough
            'LENGTH_OF_LATITUDE': 111034.61,
            'LENGTH_OF_LONGITUDE': 85393.83
        },
        'MAP_SIZES': {
            'MAP_X': 1920,
            'MAP_Y': 1080
        },
        'LABELS': {
            'fontsizes': [35, 22, 30, 18],
            'lines': [
                (150, 1080 - 55),
                (150, 1080 - 93),
                (150, 1080 - 132),
                (150, 1080 - 170)
            ]
        }
    },
    'duesseldorf': {'display': 'Düsseldorf'},
    'hamburg': {},
    'koeln': {'display': 'Köln'},
    'london': {'number_first_address': True},
    'miami': {'number_first_address': True},
    'milano': {'of_interest': True, 'display': 'Milan',
        'BOUNDS': {
            'NORTH': 45.535522,
            'SOUTH': 45.398983,
            'EAST': 9.27821,
            'WEST': 9.066236
        },
        'MAP_LIMITS': {
            # E&W values are different than home area bounds - 16:9 aspect ratio
            # map scale is 71644 for 1920x1080, use 107466 for 1280x720
            # http://render.openstreetmap.org/cgi-bin/export?bbox=8.999183,45.398983,9.345263,45.535522&scale=71644&format=png
            'NORTH': 45.535522,
            'SOUTH': 45.398983,
            'EAST': 9.345263,
            'WEST': 8.999183
        },
        'DEGREE_LENGTHS': {
            # for latitude 45.47
            'LENGTH_OF_LATITUDE': 111140.93,
            'LENGTH_OF_LONGITUDE': 78199.53
        },
        'LABELS': {
            'fontsizes': [35, 22, 30, 18, 18],
            'lines': [
                (200, 1080 - 55),
                (200, 1080 - 93),
                (200, 1080 - 132),
                (200, 1080 - 170),
                (200, 1080 - 195)
            ]
        }
    },
    'montreal': {'of_interest': True, 'number_first_address': True,
        'display': 'Montréal',
        'BOUNDS': {
            'NORTH': 45.584, # exact value is 45.58317
            'SOUTH': 45.452, # exact value is 45.452515
            'EAST': -73.548, # exact value is -73.548615
            'WEST': -73.662 # exact value is -73.661095
        },
        'MAP_LIMITS': {
            # E&W values are different than home area bounds - 16:9 aspect ratio
            # map scale is 69333 for 1920x1080
            # http://parent.tile.openstreetmap.org/cgi-bin/export?bbox=-73.7725,45.452,-73.4375,45.584&scale=69333&format=png
            'NORTH': 45.584,
            'SOUTH': 45.452,
            'EAST': -73.4375,
            'WEST': -73.7725
        },
        'DEGREE_LENGTHS': {
            # for latitude 45.518
            'LENGTH_OF_LATITUDE': 111141.87,
            'LENGTH_OF_LONGITUDE': 78133.13
        },
        'LABELS': {
            'fontsizes': [35, 22, 30, 18, 18],
            'lines': [
                (200, 1080 - 55),
                (200, 1080 - 93),
                (200, 1080 - 132),
                (200, 1080 - 170),
                (200, 1080 - 195)
            ]
        }
    },
    'muenchen': {'of_interest': True, 'display': 'Munich',
        'BOUNDS': {
            # excludes two outlying island operation areas at airport and at TUM-Garching
            'NORTH': 48.202038,
            'SOUTH': 48.077793,
            'EAST': 11.660093,
            'WEST': 11.437262
        },
        'MAP_LIMITS': {
            # E&W values are different than home area bounds - 16:9 aspect ratio
            # map scale is 68490 for 1920x1080
            # http://render.openstreetmap.org/cgi-bin/export?bbox=11.38323453,48.077793,11.71412047,48.202038&scale=68490&format=png
            'NORTH': 48.202038,
            'SOUTH': 48.077793,
            'EAST': 11.71412047,
            'WEST': 11.38323453
        },
        'DEGREE_LENGTHS': {
            # for latitude 48.14
            'LENGTH_OF_LATITUDE': 111193.01,
            'LENGTH_OF_LONGITUDE': 74423.20
        },
        'LABELS': {
            'fontsizes': [35, 22, 30, 18, 18],
            'lines': [
                (200, 1080 - 55),
                (200, 1080 - 93),
                (200, 1080 - 132),
                (200, 1080 - 170),
                (200, 1080 - 195)
            ]
        }
    },
    'portland': {'of_interest': True,
        'number_first_address': True,
        'BOUNDS': {
            'NORTH': 45.583, # exact value is 45.582718
            'SOUTH': 45.435, # exact value is 45.435555, or 45.463924 excl PCC
            'EAST': -122.557, # exact value is -122.557724
            'WEST': -122.738 # exact value is -122.73726, or -122.72915 excl PCC
        },
        'MAP_LIMITS': {
            # values are different than home area bounds - 16:9 aspect ratio
            # map scale is 1:77700 for 1920x1080
            # http://parent.tile.openstreetmap.org/cgi-bin/export?bbox=-122.83514,45.435,-122.45986,45.583&scale=77700&format=png for 1920x1080
            'NORTH': 45.583,
            'SOUTH': 45.435,
            'EAST': -122.45986,
            'WEST': -122.83514
        },
        'DEGREE_LENGTHS': {
            # for latitude 45.52
            'LENGTH_OF_LATITUDE': 111141.91,
            'LENGTH_OF_LONGITUDE': 78130.36
        },
        'LABELS': {
            'fontsizes': [30, 22, 30, 18, 18],
            'lines': [
                (20, 1080 - 50),
                (20, 1080 - 82),
                (20, 1080 - 122),
                (20, 1080 - 155),
                (20, 1080 - 180)
            ]
        }
    },
    'sandiego': {'display': 'San Diego', 'electric': 'all',
        'number_first_address': True},
    'seattle': {'of_interest': True, 'number_first_address': True,
        'BOUNDS': {
            'NORTH': 47.724, # exact value is 47.723562
            'SOUTH': 47.520, # exact value is 47.5208 - Fauntleroy Ferry
            'EAST': -122.245, # exact value is -122.24517
            'WEST': -122.437 # exact value is -122.43666
        },
        'MAP_LIMITS': {
            # values are different than home area bounds - 16:9 aspect ratio
            # map scale is 1 : 111350 for 1920x1080
            # http://parent.tile.openstreetmap.org/cgi-bin/export?bbox=-122.61,47.52,-122.072,47.724&scale=111300&format=png
            'NORTH': 47.724,
            'SOUTH': 47.520,
            'EAST': -122.072,
            'WEST': -122.610
        },
        'DEGREE_LENGTHS': {
            # for latitude 47.61
            'LENGTH_OF_LATITUDE': 111182.70,
            'LENGTH_OF_LONGITUDE': 75186.03
        },
        'LABELS': {
            'fontsizes': [35, 22, 30, 18, 18],
            'lines': [
                (400, 1080 - 55),
                (400, 1080 - 93),
                (400, 1080 - 132),
                (400, 1080 - 170),
                (400, 1080 - 195)
            ]
        },
    },
    'stuttgart': {'electric': 'all'}, 
    'toronto': {'of_interest': True, 'number_first_address': True,
        'BOUNDS': {
            'NORTH': 43.72736,
            'SOUTH': 43.625893,
            'EAST': -79.2768,
            'WEST': -79.50168
        },
        'MAP_LIMITS': {
            # values are different than home area bounds - 16:9 aspect ratio
            # map scale is 1:51614 for 1920x1080
            # http://render.openstreetmap.org/cgi-bin/export?bbox=-79.513884804,43.625893,-79.264595196,43.72736&scale=51614&format=png
            'NORTH': 43.72736,
            'SOUTH': 43.625893,
            'EAST': -79.264595196,
            'WEST': -79.513884804
        },
        'DEGREE_LENGTHS': {
            # for latitude 43.7
            'LENGTH_OF_LATITUDE': 111106.36,
            'LENGTH_OF_LONGITUDE': 80609.20
        },
        'MAP_SIZES': {
            'MAP_X' : 1920,
            'MAP_Y' : 1080
        },
        'LABELS': {
            'fontsizes': [35, 22, 30, 18],
            'lines': [
                (200, 1080 - 55),
                (200, 1080 - 93),
                (200, 1080 - 132),
                (200, 1080 - 170)
            ]
        }
    },
    'ulm': {},
    'vancouver': {'of_interest': True,
        'number_first_address': True,
        'BOUNDS': {
            # Based on operation areas and parking spots as of January 2015,
            # bounds are defined as:
            # north: North Van northern boundary, exact value 49.335808
            # south: Richmond southern boundary, exact value 49.16097
            # east: BCIT Burnaby parking lot, exact value -123.0081
            # west: UBC westernmost parking lot, exact value -123.25777
            # + 0.003 padding on all sides to account for GPS wobble.
            # This excludes parking areas at: Grouse Mtn, Horseshoe Bay, and Kwantlen Surrey and Langley campuses,
            # as these are marginal areas that would stretch the map too much in north-south dimension.
            'NORTH': 49.338808,
            'SOUTH': 49.15797,
            'EAST': -123.0051,
            'WEST': -123.26077
        },
        'MAP_LIMITS': {
            # E & W values are different than home area bounds - expanded symmetrically for 16:9 aspect ratio
            # map scale is 1 : 101947 for 1920x1080
            # http://render.openstreetmap.org/cgi-bin/export?bbox=-123.379119,49.15797,-122.886751,49.338808&scale=101947&format=png
            'NORTH': 49.338808,
            'SOUTH': 49.15797,
            'EAST': -122.886751,
            'WEST': -123.379119
        },
        'DEGREE_LENGTHS': {
            # for latitude 49.25
            'LENGTH_OF_LATITUDE': 111214.54,
            'LENGTH_OF_LONGITUDE': 72804.85
        },
        'MAP_SIZES': {
            'MAP_X' : 1920,
            'MAP_Y' : 1080
        },
        'LABELS': {
            'fontsizes': [35, 22, 30, 18],
            'lines': [
                (100, 1080 - 135),
                (100, 1080 - 173),
                (100, 1080 - 212),
                (100, 1080 - 250)
            ]
        }
    },
    'vancouver-metro': {
        # Could do a wider area Vancouver analysis including all the outlying areas.

        # The limits would be (as of January 2015):
        # north = Grouse parking / home area at 49.37522
        # south = Kwantlen Langley western campus parking spot at 49.100723
        # east = Kwantlen Langley eastern campus parking spot at -122.64428
        # west = Horseshoe Bay parking / home area at -123.2745
    },
    'washingtondc': {'display': 'Washington, D.C.',
        'number_first_address': True},
    'wien': {'of_interest': True, 'display': 'Vienna',
        'BOUNDS': {
            'NORTH': 48.29633,
            'SOUTH': 48.14736,
            'EAST': 16.48181,
            'WEST': 16.279331
            # excluded parkspots outside of main home area and at airport
        },
        'MAP_LIMITS': {
            # E&W values are different than home area bounds - 16:9 aspect ratio
            # map scale is 82237 for 1920x1080
            # http://parent.tile.openstreetmap.org/cgi-bin/export?bbox=16.181987,48.1474,16.579154,48.2963&scale=82237&format=png
            'NORTH': 48.29633,
            'SOUTH': 48.14736,
            'EAST': 16.579154,
            'WEST': 16.181987
        },
        'DEGREE_LENGTHS': {
            # for latitude 48.22
            'LENGTH_OF_LATITUDE': 111194.56,
            'LENGTH_OF_LONGITUDE': 74307.49
        },
        'LABELS': {
            'fontsizes': [35, 22, 30, 18, 18],
            'lines': [
                (200, 1080 - 55),
                (200, 1080 - 93),
                (200, 1080 - 132),
                (200, 1080 - 170),
                (200, 1080 - 195)
            ]
        }
    }
}

# fill in city data that can be assumed and autogenerated
for city, city_data in CITIES.items():
    if 'API_AVAILABLE_VEHICLES_URL' not in city_data:
        city_data['API_AVAILABLE_VEHICLES_URL'] = API_URL(loc=city)


def get_operation_areas(city):
    import requests

    API_AREAS_URL = 'https://www.car2go.com/api/v2.1/operationareas?loc={loc}&oauth_consumer_key={key}&format=json'

    r = requests.get(API_AREAS_URL.format(loc=city, key=OAUTH_KEY))

    return r.json().get('placemarks')

def get_parking_spots(city):
    import requests

    API_PARKING_URL = 'https://www.car2go.com/api/v2.1/parkingspots?loc={loc}&oauth_consumer_key={key}&format=json'

    r = requests.get(API_PARKING_URL.format(loc=city, key=OAUTH_KEY))

    return r.json().get('placemarks')

def print_operation_areas(city):
    areas = get_operation_areas(city)

    for area in areas:
        print('%s: %s zone' % (area['name'], area['zoneType']))
        print('border points: %d, bounds: %s' % (len(area['coordinates']), get_max_latlng(area)))

def print_parking_spots(city, lat_gt=False, lat_lt=False, lng_gt=False, lng_lt=False):
    spots = get_parking_spots(city)

    # mimic data format for operation area bounds
    all_coords = {'coordinates': []}

    for spot in spots:
        lat = spot['coordinates'][1]
        lng = spot['coordinates'][0]

        # filter points if requested
        if lat_gt and lat < lat_gt:
            continue
        if lat_lt and lat > lat_lt:
            continue
        if lng_gt and lng < lng_gt:
            continue
        if lng_lt and lng > lng_lt:
            continue

        # if we're here, point shouldn't be filtered, add to list
        all_coords['coordinates'].extend(spot['coordinates'])

    print('parking spots: %d, bounds: %s' % (len(all_coords['coordinates']), get_max_latlng(all_coords)))

def get_max_latlng(area):
    latitudes = []
    longitudes = []

    # collect lats and longs
    coords = area['coordinates']
    for i in range(0, len(coords), 3):
        longitudes.append(coords[i])
        latitudes.append(coords[i+1])
        # coords[i+2] is always 0 - elevation placeholder?

    return max(latitudes), min(latitudes), max(longitudes), min(longitudes)

def get_latlng_extent(city):
    areas = get_operation_areas(city)

    latitudes = []
    longitudes = []

    # collect max lats and longs across all 'operation areas'
    for area in areas:
        max_lat, min_lat, max_lng, min_lng = get_max_latlng(area)
        latitudes.append(max_lat)
        latitudes.append(min_lat)
        longitudes.append(max_lng)
        longitudes.append(min_lng)

    # return max/mins for all operation areas
    return max(latitudes), min(latitudes), max(longitudes), min(longitudes)

