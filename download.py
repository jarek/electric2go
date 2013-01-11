#!/usr/bin/env python
# coding=utf-8

import datetime
import os
import cars
import index

city = cars.get_city()

cars_text = cars.get_all_cars_text(city, force_download = True)

data_dir = os.path.dirname(os.path.realpath(__file__)) + '/data/'

f = open(data_dir + 'current_%s' % city, 'w')
print >> f, cars_text
f.close()

t = datetime.datetime.now()
if t.minute % 5 == 0:
	f = open(data_dir + '%s_%04d-%02d-%02d--%02d-%02d' % (city, t.year, t.month, t.day, t.hour, t.minute), 'w')
	print >> f, cars_text
	f.close()

print str(datetime.datetime.now()),
index.print_timer_info(cars.timer)
