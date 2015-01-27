#!/usr/bin/env python2
# coding=utf-8

from os import path


OAUTH_KEY = 'car2gowebsite'  # default key used by car2go.com

_oauth_file = path.join(path.dirname(__file__), 'oauth_key')
if path.exists(_oauth_file):
    with open(_oauth_file, 'r') as f:
        OAUTH_KEY = f.read().strip()

API_URL = 'https://www.car2go.com/api/v2.1/vehicles?loc={loc}&oauth_consumer_key=%s&format=json' % OAUTH_KEY
