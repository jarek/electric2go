# coding=utf-8

from __future__ import print_function
import datetime
import os
import time

import requests

from . import cars, systems


def head_url(url, session, extra_headers):
    if session is None:
        session = requests.Session()

    session.head(url, headers=extra_headers)

    return session


def get_url(url, session, extra_headers):
    if session is None:
        session = requests.Session()

    r = session.get(url, headers=extra_headers)

    return r.content, session


def download_one_city(city_data, session=None):
    if city_data['API_KNOCK_HEAD_URL']:
        # some APIs require we hit another URL first to prepare session
        session = head_url(city_data['API_KNOCK_HEAD_URL'],
                           session,
                           city_data['API_AVAILABLE_VEHICLES_HEADERS'])

    json_text, session = get_url(city_data['API_AVAILABLE_VEHICLES_URL'],
                                 session,
                                 city_data['API_AVAILABLE_VEHICLES_HEADERS'])

    # handle JSONP if necessary
    if 'JSONP_CALLBACK_NAME' in city_data:
        prefix = '{callback}('.format(callback=city_data['JSONP_CALLBACK_NAME'])
        suffix1 = ');'
        suffix2 = ')'

        json_text = json_text.decode('utf-8')

        if json_text.startswith(prefix):
            if json_text.endswith(suffix1):
                json_text = json_text[len(prefix):-len(suffix1)]
            elif json_text.endswith(suffix2):
                json_text = json_text[len(prefix):-len(suffix2)]

        json_text = json_text.encode('utf-8')

    return json_text, session


def save_one_city(city, timestamp_to_save, should_archive, session):
    cars_text, session = download_one_city(city, session=session)

    with open(cars.get_current_file_path(city), 'wb') as f:
        f.write(cars_text)

    if should_archive:
        with open(cars.get_file_path(city, timestamp_to_save), 'wb') as f:
            f.write(cars_text)

    return session


def get_current(city_data, max_cache_age):
    """
    Gets current data for city. Returns data from local cache file
    if available, downloads data from API otherwise.
    """
    json_text = None
    cache = False

    # see if it's already cached
    cached_data_filename = cars.get_current_file_path(city_data)
    if os.path.exists(cached_data_filename):
        cached_data_timestamp = os.path.getmtime(cached_data_filename)
        cached_data_age = time.time() - cached_data_timestamp
        if cached_data_age < max_cache_age:
            cache = cached_data_timestamp
            with open(cached_data_filename, 'rb') as f:
                json_text = f.read()

    if not json_text:
        cache = False
        json_text, session = download_one_city(city_data)
        session.close()

    return json_text, cache


def save(requested_system, requested_city, should_archive):
    failures = []

    if requested_city == 'all':
        all_cities = systems.get_all_cities(requested_system)
        cities_to_download_list = [city for key, city in all_cities.items()
                                   if city['of_interest'] or city['electric'] == 'some']
    else:
        cities_to_download_list = [systems.get_city_by_name(requested_system, requested_city)]

    t = datetime.datetime.utcnow()
    session = None
    for city in cities_to_download_list:
        try:
            session = save_one_city(city, t, should_archive, session)
        except:
            # bypass cities that fail (like Ulm did in 2015-01) without killing whole script
            failures.append((city['system'], city['name']))
            continue
    if session:
        session.close()

    return t, failures
