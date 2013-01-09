#!/usr/bin/env python
# coding=utf-8

import cgi
import pycurl
import StringIO
import simplejson as json
import time
import datetime
import index

city = 'vancouver'

cars_text = index.get_all_cars_text(city)

f = open('./data/current_%s' % city, 'w')
print >> f, cars_text
f.close()

t = datetime.datetime.now()
if t.minute % 10 == 0:
	f = open('./data/%s_%04d-%02d-%02d--%02d-%02d' % (city, t.year, t.month, t.day, t.hour, t.minute), 'w')
	print >> f, cars_text
	f.close()

index.print_timer_info()
