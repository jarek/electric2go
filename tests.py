#!/usr/bin/env python2
# coding=utf-8

from __future__ import unicode_literals
import unittest
import os
import numpy as np
import simplejson as json
from datetime import datetime

import cars
import download
import process
from analysis import graph as process_graph
from analysis import stats as process_stats
import city_helper

CITIES = cars.get_all_cities("car2go")

# TODO: we need way more tests


class DownloadTest(unittest.TestCase):
    # the following must be defined in system definitions
    test_cities = [
        ('car2go', 'wien'),  # use to test non-ASCII handling
        ('evo', 'vancouver'),
        ('drivenow', 'koeln'),
        ('communauto', 'montreal')
    ]

    def test_car2go_get_text(self):
        for city in self.test_cities:
            city_data = cars.get_all_cities(city[0])[city[1]]

            text, cache, _ = cars.get_all_cars_text(city_data, force_download=True)

            # could throw exception if JSON is malformed, test if it does
            info = json.loads(text)

            # assert there is something
            self.assertGreater(len(info), 0)

    def test_download(self):
        for city in self.test_cities:
            city_data = cars.get_all_cities(city[0])[city[1]]

            t, _ = download.save(city[0], city[1])

            file_absolute = cars.get_file_path(city_data, t)
            file_current = cars.get_current_filename(city_data)

            self.assertTrue(os.path.exists(file_absolute))
            self.assertTrue(os.path.exists(file_current))

    def test_cache(self):
        for city in self.test_cities:
            city_data = cars.get_all_cities(city[0])[city[1]]

            # warm up the cache
            _, _ = download.save(city[0], city[1])

            text, cache, _ = cars.get_all_cars_text(city_data)

            # check we've gotten a cached file
            self.assertTrue(cache != False and cache > 0)

            info = json.loads(text)  # check the json can be parsed

            self.assertGreater(len(info), 0)  # check there is something


class StatsTest(unittest.TestCase):
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
                "expected_stats": {
                    "total vehicles": 296,
                    "total trips": 1737,
                    "starting time": datetime(2015, 4, 28, 8, 0, 0),
                    "ending time": datetime(2015, 4, 30, 7, 59, 0),
                    "time elapsed seconds": 172740,
                    "trips per car median": 6,
                    "distance per trip quartile 25": 0.6388606347651411,
                    "duration per trip quartile 75": 32,
                    "weird trip count": 64
                },
                "expected_dataframes": {
                    0: {
                        "turn": "2015-04-28T08:00:00",
                        "len_cars": 287
                    },
                    2009: {
                        "len_cars": 272
                    },
                    2010: {
                        "len_cars": 270
                    },
                    -1: {
                        "index": 2879,
                        "turn": "2015-04-30T07:59:00",
                        "len_cars": 285
                    }
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
                "expected_stats": {
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
                },
                "expected_dataframes": {
                    0: {
                        "index": 0,
                        "turn": "2015-05-16T11:00:00",
                        "len_trips": 0
                    },
                    250: {
                        "index": 250,
                        "turn": "2015-05-16T15:10:00",
                        "len_cars": 215
                    },
                    1999: {
                        "len_cars": 188
                    },
                    2000: {
                        "len_cars": 187,
                        "len_trips": 1
                    },
                    -1: {
                        "turn": "2015-05-18T10:59:00",
                        "len_cars": 226,
                        "len_trips": 0,
                    }
                }
            }
    }

    @classmethod
    def setUpClass(cls):
        # read in data just once
        cls.results = {}

        for dataset_name in cls.datasets:
            params = cls.datasets[dataset_name]["params"]

            result_dict = process.batch_load_data(**params)

            cls.results[dataset_name] = result_dict

    def test_stats_for_sample_datasets(self):
        for dataset_name in self.datasets:
            exp_stats = self.datasets[dataset_name]["expected_stats"]

            stats = process_stats.stats_dict(self.results[dataset_name])

            for category in exp_stats:
                self.assertEqual(exp_stats[category], stats[category],
                                 "{name} {cat}: expected {exp}, got {got}".format(
                                     name=dataset_name, cat=category,
                                     exp=exp_stats[category], got=stats[category]))

    def test_dataframes_for_sample_datasets(self):
        for dataset_name in self.datasets:
            exp_dataframes = self.datasets[dataset_name]["expected_dataframes"]

            # immediately evaluating a generator is kinda rude, but this is
            # only for testing, where I have expected values for
            # specific indexes. don't do this in non-test code obviously.
            data_frames = list(process.build_data_frames(self.results[dataset_name]))

            for i in exp_dataframes:
                exp_frame = exp_dataframes[i]
                if 'index' in exp_frame:
                    self.assertEqual(exp_frame['index'], data_frames[i][0],
                                     "{name} {frame} turn: expected {exp}, got {got}".format(
                                         name=dataset_name, frame=i,
                                         exp=exp_frame['index'], got=data_frames[i][0]))
                if 'turn' in exp_frame:
                    self.assertEqual(exp_frame['turn'], data_frames[i][1].isoformat(),
                                     "{name} {frame} turn: expected {exp}, got {got}".format(
                                         name=dataset_name, frame=i,
                                         exp=exp_frame['turn'], got=data_frames[i][1].isoformat()))
                if 'len_cars' in exp_frame:
                    self.assertEqual(exp_frame['len_cars'], len(data_frames[i][2]),
                                     "{name} {frame} len_cars: expected {exp}, got {got}".format(
                                         name=dataset_name, frame=i,
                                         exp=exp_frame['len_cars'], got=len(data_frames[i][2])))
                if 'len_trips' in exp_frame:
                    self.assertEqual(exp_frame['len_trips'], len(data_frames[i][3]),
                                     "{name} {frame} len_trips: expected {exp}, got {got}".format(
                                         name=dataset_name, frame=i,
                                         exp=exp_frame['len_trips'], got=len(data_frames[i][3])))


class HelperFunctionsTest(unittest.TestCase):
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

