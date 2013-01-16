#!/usr/bin/env python
# coding=utf-8

import datetime
import os
import sys
import cars
import index

if len(sys.argv) > 1 and sys.argv[1].lower() == 'all':
	cities = [city for city in cars.CITIES \
		if cars.CITIES[city]['electric'] == 'some' 
		or cars.CITIES[city]['of_interest'] == True]
else:
	cities = [ cars.get_city() ]

t = datetime.datetime.now()
for city in cities:
	cars_text = cars.get_all_cars_text(city, force_download = True)

	f = open(cars.data_dir + 'current_%s' % city, 'w')
	print >> f, cars_text
	f.close()

	if cars.CITIES[city]['of_interest'] == True and t.minute % 5 == 0:
		filename = cars.filename_format % (city, t.year, t.month, t.day, t.hour, t.minute)
		f = open(cars.data_dir + filename, 'w')
		print >> f, cars_text
		f.close()

print str(t),
index.print_timer_info(cars.timer)
