#!/usr/bin/env python2
# coding=utf-8

import datetime
import sys
from os import path
import cars
import index

if len(sys.argv) < 3:
    sys.exit('!!! must specify system and city to download (or system and "all")')

requested_system = sys.argv[1].lower()
requested_city = sys.argv[2].lower()

all_cities = cars.get_all_cities(requested_system)

if requested_city == 'all':
    cities_to_download = {city_key: city_data for city_key, city_data in all_cities.items()
                          if city_data['of_interest'] or city_data['electric'] == 'some'}
else:
    cities_to_download = {requested_city: all_cities[requested_city]}

t = datetime.datetime.utcnow()
for city_name, city_data in cities_to_download.items():
    try:
        city_obj = {'name': city_name, 'data': city_data}

        cars_text, cache = cars.get_all_cars_text(city_obj, force_download=True)

        with open(cars.get_current_filename(city_data), 'w') as f:
            f.write(cars_text)

        # also save data every DATA_COLLECTION_INTERVAL_MINUTES
        if t.minute % cars.DATA_COLLECTION_INTERVAL_MINUTES == 0:
            filename = cars.filename_format % (city_name, t.year, t.month, t.day, t.hour, t.minute)
            filepath = path.join(cars.get_data_dir(requested_system), filename)

            with open(filepath, 'w') as f:
                f.write(cars_text)
    except:
        # bypass cities that fail (like Ulm did in 2015-01) without killing whole script
        print '!!! could not download or save information for city: %s' % city_name
        continue


print str(t),
index.print_timer_info(cars.timer)

