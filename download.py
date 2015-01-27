#!/usr/bin/env python2
# coding=utf-8

import datetime
import os
import sys
import cars
from car2go import city
import index

if len(sys.argv) > 1 and sys.argv[1].lower() == 'all':
    cities = [city_key for city_key in city.CITIES \
        if city.CITIES[city_key]['electric'] == 'some' 
        or city.CITIES[city_key]['of_interest'] == True]
else:
    cities = [ cars.get_city() ]

t = datetime.datetime.now()
for city in cities:
    try:
        cars_text,cache = cars.get_all_cars_text(city, force_download = True)
        current_filename = cars.data_dir + 'current_%s' % city
        with open(current_filename, 'w') as f:
            f.write(cars_text)

        # save all information downloaded for now
        #if cars.CITIES[city]['of_interest'] == True \
        if True \
                and t.minute % cars.DATA_COLLECTION_INTERVAL_MINUTES == 0:
            filename = cars.filename_format % (city, t.year, t.month, t.day, t.hour, t.minute)
            with open(cars.data_dir + filename, 'w') as f:
                f.write(cars_text)
    except:
        # bypass cities that fail (like Ulm did in 2015-01) without killing whole script
        print '!!! could not download or save information for city: %s' % city
        continue


print str(t),
index.print_timer_info(cars.timer)

