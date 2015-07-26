# coding=utf-8

from os import path


API_KEY = ''  # provide key either here or in file "api_key"

_api_key_file = path.join(path.dirname(__file__), 'api_key')
if path.exists(_api_key_file):
    with open(_api_key_file, 'r') as f:
        API_KEY = f.read().strip()

API_ROUTE_ALL_BUSES_URL = lambda route:\
    'http://api.translink.ca/rttiapi/v1/buses?routeNo={route}&apikey={key}'.format(key=API_KEY, route=route)

API_ROUTE_ALL_BUSES_HEADERS = {'Accept': 'application/json'}
