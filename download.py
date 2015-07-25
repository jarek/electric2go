#!/usr/bin/env python3
# coding=utf-8

from __future__ import print_function
import datetime
import sys

import cars


def save_one_city(city, t, session=None):
    cars_text, _, session = cars.get_all_cars_text(city,
                                                   force_download=True,
                                                   session=session)

    with open(cars.get_current_filename(city), 'wb') as f:
        f.write(cars_text)

    # also save data every DATA_COLLECTION_INTERVAL_MINUTES
    if t.minute % cars.DATA_COLLECTION_INTERVAL_MINUTES == 0:
        with open(cars.get_file_path(city, t), 'wb') as f:
            f.write(cars_text)

    return session


def save(requested_system, requested_city):
    failures = []

    all_cities = cars.get_all_cities(requested_system)

    if requested_city == 'all':
        cities_to_download_list = [city for key, city in all_cities.items()
                                   if city['of_interest'] or city['electric'] == 'some']
    else:
        cities_to_download_list = [all_cities[requested_city]]

    t = datetime.datetime.utcnow()
    session = None
    for city in cities_to_download_list:
        try:
            session = save_one_city(city, t, session=session)
        except:
            # bypass cities that fail (like Ulm did in 2015-01) without killing whole script
            failures.append((city['system'], city['name']))
            continue

    return t, failures


def process_commandline():
    if len(sys.argv) < 3:
        sys.exit('!!! must specify system and city to download (or system and "all")')

    requested_system = sys.argv[1].lower()
    requested_city = sys.argv[2].lower()

    t, failures = save(requested_system, requested_city)

    end_time = datetime.datetime.utcnow()

    print('{timestamp} downloading {system} {city}, finished {end}'.format(
        timestamp=str(t), system=requested_system, city=requested_city, end=end_time))

    for failed in failures:
        message = '!!! could not download or save information for system {system} city {city}'
        print(message.format(system=failed[0], city=failed[1]))


if __name__ == '__main__':
    process_commandline()
