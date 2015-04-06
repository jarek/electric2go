#!/usr/bin/env python2
# coding=utf-8

from . import API_AVAILABLE_VEHICLES_URL


CITIES = {
    'vancouver': {
        'of_interest': True,
        'API_AVAILABLE_VEHICLES_URL': API_AVAILABLE_VEHICLES_URL
    }
}


KNOWN_CITIES = [city for city in CITIES]
# uncomment once we have map data - currently map tasks will fail, but we can still get stats
"""if ('BOUNDS' in CITIES[city]
        and 'MAP_LIMITS' in CITIES[city]
        and 'DEGREE_LENGTHS' in CITIES[city]
        and 'MAP_SIZES' in CITIES[city]
        and 'LABELS' in CITIES[city])
    ]"""
