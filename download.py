#!/usr/bin/env python
# coding=utf-8

import datetime
import cars
import index

city = cars.get_city()

cars_text = cars.get_all_cars_text(city, force_download = True)

f = open('./data/current_%s' % city, 'w')
print >> f, cars_text
f.close()

t = datetime.datetime.now()
if t.minute % 10 == 0:
	f = open('./data/%s_%04d-%02d-%02d--%02d-%02d' % (city, t.year, t.month, t.day, t.hour, t.minute), 'w')
	print >> f, cars_text
	f.close()

index.print_timer_info(cars.timer)
