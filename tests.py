#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals
import unittest
import numpy as np

import process
import cars

class process_helper_functions(unittest.TestCase):
    def test_is_latlng_in_bounds(self):
        VALUES = {
            'vancouver': [49.25199,-123.06672],
            'toronto': [43.66666,-79.33333],
            'berlin': [52.50752,13.37313],
            'buenosaires': [-34.3,-58.5]
        }

        self.assertTrue(process.is_latlng_in_bounds('vancouver', 
            VALUES['vancouver']))
        self.assertTrue(process.is_latlng_in_bounds('toronto', 
            VALUES['toronto']))
        self.assertTrue(process.is_latlng_in_bounds('berlin', 
            VALUES['berlin']))
        self.assertTrue(process.is_latlng_in_bounds('buenosaires', 
            VALUES['buenosaires']))

    def test_map_latitude(self):
        toronto_res = process.map_latitude('toronto', np.array([43.65]))
        self.assertGreaterEqual(toronto_res, 0)
        self.assertLessEqual(toronto_res, process.MAP_SIZES['toronto']['MAP_Y'])

        berlin_res = process.map_latitude('berlin', np.array([52.5]))
        self.assertGreaterEqual(berlin_res, 0)
        self.assertLessEqual(berlin_res, process.MAP_SIZES['berlin']['MAP_Y'])

    def test_map_longitude(self):
        toronto_res = process.map_longitude('toronto', np.array([-79.3]))
        self.assertGreaterEqual(toronto_res, 0)
        self.assertLessEqual(toronto_res, process.MAP_SIZES['toronto']['MAP_X'])

        berlin_res = process.map_longitude('berlin', np.array([13.5]))
        self.assertGreaterEqual(berlin_res, 0)
        self.assertLessEqual(berlin_res, process.MAP_SIZES['berlin']['MAP_X'])

 
if __name__ == '__main__':
    unittest.main()

