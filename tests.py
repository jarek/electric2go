#!/usr/bin/env python2
# coding=utf-8

from __future__ import unicode_literals
import unittest
import numpy as np

from car2goprocess import graph as process_graph
from city import CITIES
import city_helper

class process_helper_functions(unittest.TestCase):
    def test_is_latlng_in_bounds(self):
        VALUES = {
            'vancouver': [49.25199,-123.06672],
            'toronto': [43.66666,-79.33333],
            'wien': [48.2,16.3667],
            'buenosaires': [-34.3,-58.5]
        }

        # test northern and western hemisphere
        self.assertTrue(city_helper.is_latlng_in_bounds(CITIES['vancouver'],
                                                        VALUES['vancouver']))
        self.assertTrue(city_helper.is_latlng_in_bounds(CITIES['toronto'],
                                                        VALUES['toronto']))

        # test northern and eastern hemisphere
        self.assertTrue(city_helper.is_latlng_in_bounds(CITIES['wien'],
                                                        VALUES['wien']))

        # TODO: test correctness of calculation for southern hemisphere
        #self.assertTrue(city_helper.is_latlng_in_bounds(city.CITIES, 'buenosaires',
        #                                                VALUES['buenosaires']))

    def test_map_latitude(self):
        toronto_res = process_graph.map_latitude('toronto', np.array([43.65]))
        self.assertGreaterEqual(toronto_res, 0)
        self.assertLessEqual(toronto_res, CITIES['toronto']['MAP_SIZES']['MAP_Y'])

        wien_res = process_graph.map_latitude('wien', np.array([48.2]))
        self.assertGreaterEqual(wien_res, 0)
        self.assertLessEqual(wien_res, CITIES['wien']['MAP_SIZES']['MAP_Y'])

    def test_map_longitude(self):
        toronto_res = process_graph.map_longitude('toronto', np.array([-79.3]))
        self.assertGreaterEqual(toronto_res, 0)
        self.assertLessEqual(toronto_res, CITIES['toronto']['MAP_SIZES']['MAP_X'])

        wien_res = process_graph.map_longitude('wien', np.array([16.4]))
        self.assertGreaterEqual(wien_res, 0)
        self.assertLessEqual(wien_res, CITIES['wien']['MAP_SIZES']['MAP_X'])

 
if __name__ == '__main__':
    unittest.main()

