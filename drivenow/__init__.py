#!/usr/bin/env python2
# coding=utf-8

from os import path


API_KEY = 'adf51226795afbc4e7575ccc124face7'  # default key used by drivenow.com

_api_key_file = path.join(path.dirname(__file__), 'api_key')
if path.exists(_api_key_file):
    with open(_api_key_file, 'r') as f:
        API_KEY = f.read().strip()

API_AVAILABLE_VEHICLES_URL = lambda loc: 'https://api2.drive-now.com/cities/{loc}?expand=full'.format(loc=loc)

API_AVAILABLE_VEHICLES_HEADERS = {'X-Api-Key': API_KEY}
