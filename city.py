#!/usr/bin/env python2
# coding=utf-8


API_AREAS_URL = 'https://www.car2go.com/api/v2.1/operationareas?loc={loc}&oauth_consumer_key={key}&format=json'

# DEGREE_LENGTHs come http://www.csgnetwork.com/degreelenllavcalc.html
# could calculate ourselves but meh. would need city's latitude

# for verification, check that:
# MAP_Y_DIMENSION / MAP_X_DIMENSION / (NORTH-SOUTH)/(EAST-WEST) ~= LENGTH_OF_LATITUDE / LENGTH_OF_LONGITUDE
# e.g. for Portland:
# 1080/1920 / (45.583-45.435)/(122.83514-122.45986) ~= 111141.91 / 78130.36
# 0.5625 / 0.394372202 = 1.426317568 ~= 1.422518852

CITIES = {
    'amsterdam': {'electric': 'all'},
    'austin': {'electric': 'some', 'number_first_address': True,
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
            'NORTH': 51.088425,
            'SOUTH': 50.984936,
            'EAST': -113.997314,
            'WEST': -114.16401
        },
        'MAP_LIMITS': {
            'NORTH': 51.088425,
            'SOUTH': 50.984936,
            'EAST': -113.997314,
            'WEST': -114.16401
        },
        'DEGREE_LENGTHS': {
            # for latitude 51.04
            'LENGTH_OF_LATITUDE': 111249.00,
            'LENGTH_OF_LONGITUDE': 70137.28
        },
        'MAP_SIZES': {
            # 978/991 / (51.088425-50.984936)/(114.16401-113.997314) ~= 111249.00 / 70137.28
            # 0.986881937 / 0.620824735 = 1.589630505 ~= 1.586160741
            'MAP_X': 991,
            'MAP_Y': 978
        },
        'LABELS': {
            'fontsize': 15,
            'lines': [
                (991 * 0.75, 978 - 120),
                (991 * 0.75, 978 - 145),
                (991 * 0.75, 978 - 170)
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
    'portland': {'of_interest': True, 'electric': 'some', 
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
            'NORTH': 43.72736,
            'SOUTH': 43.625893,
            'EAST': -79.2768,
            'WEST': -79.50168
        },
        'DEGREE_LENGTHS': {
            # for latitude 43.7
            'LENGTH_OF_LATITUDE': 111106.36,
            'LENGTH_OF_LONGITUDE': 80609.20
        },
        'MAP_SIZES': {
            # 615/991 / (43.72736-43.625893)/(79.50168-79.2768) ~= 111106.36 / 80609.20
            # 0.620585267 / 0.451205087 = 1.375395103 ~= 1.37833349
            'MAP_X' : 991,
            'MAP_Y' : 615
        },
        'LABELS': {
            'fontsize': 15,
            'lines': [
                (991 * 0.75, 160),
                (991 * 0.75, 130),
                (991 * 0.75, 100)
            ]
        }
    },
    'ulm': {},
    'vancouver': {'of_interest': True, 'electric': 'some',
        'number_first_address': True,
        'BOUNDS': {
            'NORTH': 49.336, # exact value 49.335735
            'SOUTH': 49.224, # exact value 49.224716
            'EAST':  -123.031, # exact value -123.03196
            'WEST':  -123.252
            # limit of home area is -123.21545; westernmost parking spot 
            # at UBC is listed as centered on -123.2515
            
            # there's also parkspots in Richmond and Langley,
            # I am ignoring them to make map more compact.
        },
        'MAP_LIMITS': {
            # E & W values are different than home area bounds - 16:9 aspect ratio
            # map scale is 1 : 63200 for 1920x1080
            # http://parent.tile.openstreetmap.org/cgi-bin/export?bbox=-123.29415,49.224,-122.98885,49.336&scale=63200&format=png
            'NORTH': 49.336,
            'SOUTH': 49.224,
            'EAST':  -122.98885,
            'WEST':  -123.29415
        },
        'DEGREE_LENGTHS': {
            # for latitude 49.28
            'LENGTH_OF_LATITUDE': 111215.12,
            'LENGTH_OF_LONGITUDE': 72760.72
        },
        'LABELS': {
            'fontsizes': [35, 22, 30, 18, 18],
            'lines': [
                (20, 1080 - 55),
                (20, 1080 - 93),
                (20, 1080 - 132),
                (20, 1080 - 170),
                (20, 1080 - 195)
            ]
        }
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
for city in CITIES:
    if not 'display' in CITIES[city]:
        CITIES[city]['display'] = city.title()
    if not 'electric' in CITIES[city]:
        CITIES[city]['electric'] = False
    if not 'of_interest' in CITIES[city]:
        CITIES[city]['of_interest'] = False
    if not 'number_first_address' in CITIES[city]:
        CITIES[city]['number_first_address'] = False
    if not 'MAP_SIZES' in CITIES[city]:
        CITIES[city]['MAP_SIZES'] = { 'MAP_X': 1920, 'MAP_Y': 1080 }

KNOWN_CITIES = [
    city for city in CITIES
    if ('BOUNDS' in CITIES[city]
        and 'MAP_LIMITS' in CITIES[city]
        and 'DEGREE_LENGTHS' in CITIES[city]
        and 'MAP_SIZES' in CITIES[city]
        and 'LABELS' in CITIES[city])
    ]


def get_operation_areas(city):
    import cars
    import json

    data_text = cars.get_URL(API_AREAS_URL.format(loc = city, key = cars.OAUTH_KEY))

    return json.loads(data_text).get('placemarks')

def get_latlng_extent(city):
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

def is_latlng_in_bounds(city, lat, lng = False):
    if lng == False:
        lng = lat[1]
        lat = lat[0]

    is_lat = CITIES[city]['BOUNDS']['SOUTH'] <= lat <= CITIES[city]['BOUNDS']['NORTH']
    is_lng = CITIES[city]['BOUNDS']['WEST'] <= lng <= CITIES[city]['BOUNDS']['EAST']

    return is_lat and is_lng

def get_pixel_size(city):
    # find the length in metres represented by one pixel on graph in both lat and lng direction

    city_data = CITIES[city]

    lat_range = city_data['MAP_LIMITS']['NORTH'] - city_data['MAP_LIMITS']['SOUTH']
    lat_in_m = lat_range * city_data['DEGREE_LENGTHS']['LENGTH_OF_LATITUDE']
    pixel_in_lat_m = lat_in_m / city_data['MAP_SIZES']['MAP_Y']

    lng_range = city_data['MAP_LIMITS']['EAST'] - city_data['MAP_LIMITS']['WEST']
    lng_in_m = lng_range * city_data['DEGREE_LENGTHS']['LENGTH_OF_LONGITUDE']
    pixel_in_lng_m = lng_in_m / city_data['MAP_SIZES']['MAP_X']

    return pixel_in_lat_m, pixel_in_lng_m

def get_mean_pixel_size(city):
    # find the length in metres represented by one pixel on graph

    # take mean of latitude- and longitude-based numbers, 
    # which is not quite correct but more than close enough for most uses

    pixel_in_m = get_pixel_size(city)

    return (pixel_in_m[0] + pixel_in_m[1]) / 2 

