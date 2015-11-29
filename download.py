#!/usr/bin/env python3
# coding=utf-8

from __future__ import print_function
import datetime
import time
import sys

import requests

import cars


def head_url(url, session, extra_headers):
    htime1 = time.time()

    if session is None:
        session = requests.Session()

    session.head(url, headers=extra_headers)

    htime2 = time.time()
    cars.timer.append(['http head, ms', (htime2-htime1)*1000.0])

    return session


def get_url(url, session, extra_headers):
    htime1 = time.time()

    if session is None:
        session = requests.Session()

    r = session.get(url, headers=extra_headers)

    htime2 = time.time()
    cars.timer.append(['http get, ms', (htime2-htime1)*1000.0])

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


def save(requested_system, requested_city, should_archive):
    failures = []

    if requested_city == 'all':
        all_cities = cars.get_all_cities(requested_system)
        cities_to_download_list = [city for key, city in all_cities.items()
                                   if city['of_interest'] or city['electric'] == 'some']
    else:
        cities_to_download_list = [cars.get_city_by_name(requested_system, requested_city)]

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


def process_commandline():
    if len(sys.argv) < 3:
        sys.exit('!!! must specify system and city to download (or system and "all")')

    requested_system = sys.argv[1].lower()
    requested_city = sys.argv[2].lower()

    if len(sys.argv) > 3:
        requested_archive = (sys.argv[3].lower() == 'archive')
    else:
        requested_archive = False

    t, failures = save(requested_system, requested_city, should_archive=requested_archive)

    end_time = datetime.datetime.utcnow()

    print('{timestamp} downloading {system} {city}, finished {end}'.format(
        timestamp=str(t), system=requested_system, city=requested_city, end=end_time))

    for failed in failures:
        message = '!!! could not download or save information for system {system} city {city}'
        print(message.format(system=failed[0], city=failed[1]))


if __name__ == '__main__':
    process_commandline()
