# coding=utf-8

from os import path


try:
    with open(path.join(path.dirname(__file__), 'api_key'), 'r') as f:
        API_KEY = f.read().strip()
except IOError:
    API_KEY = ''


# we pretend that individual routes are "cities" - the abstraction holds otherwise
CITIES = {
    '010': {
        'of_interest': True
    },
    '099': {
        'of_interest': True
    },
    '020': {
        'of_interest': True
    },
    '005': {
        'of_interest': True
    }
}

API_URL = 'http://api.translink.ca/rttiapi/v1/buses?routeNo={route}&apikey={key}'

# fill in data that is constant for all routes
for route_number, route_data in CITIES.items():
    if 'API_AVAILABLE_VEHICLES_URL' not in route_data:
        route_data['API_AVAILABLE_VEHICLES_URL'] = API_URL.format(key=API_KEY, route=route_number)

    if 'API_AVAILABLE_VEHICLES_HEADERS' not in route_data:
        route_data['API_AVAILABLE_VEHICLES_HEADERS'] = {'Accept': 'application/json'}
