#!/usr/bin/env python2
# coding=utf-8

from __future__ import unicode_literals
import unittest
import numpy as np
from datetime import datetime

import cars
import process
from analysis import graph as process_graph
from analysis import stats as process_stats
import city_helper

CITIES = cars.get_all_cities("car2go")

# TODO: we need way more tests

class stats_test(unittest.TestCase):
    def test_stats_for_sample_datasets(self):
        # This is hardcoded to a dataset I have, so won't be useful for anyone else.
        # Sorry! But it's worth it for me. Can be adapted to a dataset you have.
        # TODO: generate a sample dataset and test against that

        datasets = {
            "columbus": {
                "params": {
                    "system": "car2go",
                    "city": "columbus",
                    "file_dir": "/home/jarek/car2go-columbus/extracted/",
                    "starting_time": datetime(2015, 4, 28, 8, 0, 0),
                    "max_files": 2880,
                    "max_skip": 0,
                    "time_step": 1
                },
                "expected":  {
                    "total vehicles": 296,
                    "total trips": 1737,
                    "starting time": datetime(2015, 4, 28, 8, 0, 0),
                    "ending time": datetime(2015, 4, 30, 7, 59, 0),
                    "time elapsed seconds": 172740,
                    "trips per car median": 6,
                    "distance per trip quartile 25": 0.6388606347651411,
                    "duration per trip quartile 75": 32,
                    "weird trip count": 64
                }
            },
            "vancouver": {
                "params": {
                    "system": "evo",
                    "city": "vancouver",
                    "file_dir": "/home/jarek/evo-vancouver/vancouver_2015-05-1618/",
                    "starting_time": datetime(2015, 5, 16, 11, 0, 0),
                    "max_files": 2880,
                    "max_skip": 0,
                    "time_step": 1
                },
                "expected":  {
                    "total vehicles": 238,
                    "total trips": 1967,
                    "starting time": datetime(2015, 5, 16, 11, 0, 0),
                    "ending time": datetime(2015, 5, 18, 10, 59, 0),
                    "time elapsed seconds": 172740,
                    "utilization ratio": 0.12329940659834618,
                    "trips per car per day quartile 25": 1.6255644320944773,
                    "distance per trip quartile 25": 0.3909876034341634,
                    "duration per trip quartile 75": 40,
                    "weird trip count": 103
                }
            }
        }

        for dataset_name in datasets:
            params = datasets[dataset_name]["params"]
            expected = datasets[dataset_name]["expected"]

            (_data_frames, _all_positions, all_trips,
             trips_by_vin, ending_time, _total_frames) = process.batch_load_data(**params)

            stats = process_stats.stats_dict(all_trips, trips_by_vin.keys(), params["starting_time"], ending_time)

            for category in expected:
                self.assertEqual(expected[category], stats[category],
                                 "{name} {cat}: expected {exp}, got {got}".format(
                                     name=dataset_name, cat=category,
                                     exp=expected[category], got=stats[category]))


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
        toronto_res = process_graph.map_latitude(CITIES['toronto'], np.array([43.65]))
        self.assertGreaterEqual(toronto_res, 0)
        self.assertLessEqual(toronto_res, CITIES['toronto']['MAP_SIZES']['MAP_Y'])

        wien_res = process_graph.map_latitude(CITIES['wien'], np.array([48.2]))
        self.assertGreaterEqual(wien_res, 0)
        self.assertLessEqual(wien_res, CITIES['wien']['MAP_SIZES']['MAP_Y'])

    def test_map_longitude(self):
        toronto_res = process_graph.map_longitude(CITIES['toronto'], np.array([-79.3]))
        self.assertGreaterEqual(toronto_res, 0)
        self.assertLessEqual(toronto_res, CITIES['toronto']['MAP_SIZES']['MAP_X'])

        wien_res = process_graph.map_longitude(CITIES['wien'], np.array([16.4]))
        self.assertGreaterEqual(wien_res, 0)
        self.assertLessEqual(wien_res, CITIES['wien']['MAP_SIZES']['MAP_X'])

 
if __name__ == '__main__':
    unittest.main()

