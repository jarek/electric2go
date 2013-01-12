#!/usr/bin/env python
# coding=utf-8

import datetime
import os
import cars
import index

city = cars.get_city()

cars_text = cars.get_all_cars_text(city, force_download = True)

f = open(cars.data_dir + 'current_%s' % city, 'w')
print >> f, cars_text
f.close()

t = datetime.datetime.now()
if t.minute % 5 == 0:
	f = open(cars.data_dir + cars.filename_format % (city, t.year, t.month, t.day, t.hour, t.minute), 'w')
	print >> f, cars_text
	f.close()

print str(datetime.datetime.now()),
index.print_timer_info(cars.timer)
