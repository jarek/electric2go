#!/usr/bin/env python3
# coding=utf-8

from __future__ import unicode_literals
import unittest
import os
import numpy as np
import json
import csv
from subprocess import Popen, PIPE
from datetime import datetime

from electric2go import cars, download, systems
from electric2go.analysis import normalize, merge, generate
from electric2go.analysis import graph as process_graph
from electric2go.analysis import stats as process_stats

CITIES = systems.get_all_cities("car2go")

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
            city_data = systems.get_city_by_name(city[0], city[1])

            text, session = download.download_one_city(city_data)
            session.close()

            # could throw exception if JSON is malformed, test if it does
            info = json.loads(text.decode('utf-8'))

            # assert there is something
            self.assertGreater(len(info), 0)

    def test_download(self):
        for city in self.test_cities:
            city_data = systems.get_city_by_name(city[0], city[1])

            t, _ = download.save(city[0], city[1], should_archive=True)

            file_absolute = cars.get_file_path(city_data, t)
            file_current = cars.get_current_file_path(city_data)

            self.assertTrue(os.path.exists(file_absolute))
            self.assertTrue(os.path.exists(file_current))

    def test_download_create_dir(self):
        # tests that script will attempt to create data directories
        # if they don't exist
        import shutil

        city_data = {'system': 'sharengo', 'name': 'milano'}
        data_dir = cars.get_data_dir(city_data)

        # delete if already exists
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)

        # download
        t, _ = download.save(city_data['system'], city_data['name'], False)
        file_current = cars.get_current_file_path(city_data)

        # test it was downloaded
        self.assertTrue(os.path.exists(file_current))

    def test_cache(self):
        for city in self.test_cities:
            city_data = systems.get_city_by_name(city[0], city[1])

            # warm up the cache
            _, _ = download.save(city[0], city[1], should_archive=False)

            text, cache = download.get_current(city_data, max_cache_age=30)

            # check we've gotten a cached file
            self.assertTrue(cache != False and cache > 0)

            info = json.loads(text.decode('utf-8'))  # check the json can be parsed

            self.assertGreater(len(info), 0)  # check there is something


class StatsTest(unittest.TestCase):
    # This is hardcoded to a dataset I have, so won't be useful for anyone else.
    # Sorry! But it's worth it for me. Can be adapted to a dataset you have.
    # TODO: generate a sample dataset and test against that

    datasets = {
            "columbus": {
                # This is defined by specifying path to the first file.
                # Command-line will typically be invoked like this.
                "params": {
                    "system": "car2go",
                    "starting_filename": "/home/jarek/car2go-columbus/extracted/columbus_2015-04-28--08-00",
                    "starting_time": None,
                    "ending_time": datetime(2015, 4, 30, 7, 59, 0),
                    "time_step": 60
                },
                "expected_stats": {
                    "total vehicles": 296,
                    "total trips": 1737,
                    "starting time": datetime(2015, 4, 28, 8, 0, 0),
                    "ending time": datetime(2015, 4, 30, 7, 59, 0),
                    "time elapsed seconds": 172740.0,
                    "trips per car median": 6.0,
                    "distance per trip quartile 25": 0.638860634765,
                    "duration per trip quartile 75": 32.0,
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
                },
                "expected_metadata": {
                    "city": "columbus",
                    "system": "car2go"
                }
            },
            "vancouver": {
                # This is defined by specifying path to the first file.
                # Command-line will typically be invoked like this.
                "params": {
                    "system": "evo",
                    "starting_filename": "/home/jarek/evo-vancouver/vancouver_2015-05-1618/vancouver_2015-05-16--11-00",
                    "starting_time": None,
                    "ending_time": datetime(2015, 5, 18, 10, 59, 0),
                    "time_step": 60
                },
                "expected_stats": {
                    "total vehicles": 238,
                    "total trips": 1967,
                    "starting time": datetime(2015, 5, 16, 11, 0, 0),
                    "ending time": datetime(2015, 5, 18, 10, 59, 0),
                    "time elapsed seconds": 172740.0,
                    "utilization ratio": 0.1232994066,
                    "trips per car per day quartile 25": 1.625564432,
                    "distance per trip quartile 25": 0.3909876034,
                    "duration per trip quartile 75": 40.0,
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
                },
                "expected_metadata": {
                    "city": "vancouver",
                    "system": "evo"
                }
            },
            "vancouver_archive": {
                # This is defined by specifying path to an archive.
                # Command-line will typically be invoked like this.

                # All expected data should be the same as in vancouver_files
                "params": {
                    "system": "evo",
                    "starting_filename": "/home/jarek/evo-vancouver/vancouver_2015-06-19.tgz",
                    "starting_time": None,
                    "ending_time": None,
                    "time_step": 60
                },
                "expected_stats": {
                    "total vehicles": 238,
                    "total trips": 1333,
                    "starting time": datetime(2015, 6, 19, 0, 0, 0),
                    "ending time": datetime(2015, 6, 19, 23, 59, 0),
                    "time elapsed seconds": 86340.0,
                    "utilization ratio": 0.1325850702,
                    "trips per car per day quartile 25": 3.002084781,
                    "distance per trip quartile 25": 0.1563771331,
                    "duration per trip quartile 75": 37.0,
                    "weird trip count": 37
                },
                "expected_dataframes": {
                    0: {
                        "index": 0,
                        "turn": "2015-06-19T00:00:00",
                        "len_trips": 0,
                        "len_cars": 162
                    },
                    -1: {
                        "index": 1439,
                        "turn": "2015-06-19T23:59:00",
                        "len_cars": 165
                    }
                },
                "expected_metadata": {
                    "city": "vancouver",
                    "system": "evo",
                    "starting_time": datetime(2015, 6, 19, 0, 0, 0),
                    "ending_time": datetime(2015, 6, 19, 23, 59, 0),
                    "missing": [
                        datetime(2015, 6, 19, 6, 46, 0),
                        datetime(2015, 6, 19, 7, 9, 0),
                        datetime(2015, 6, 19, 17, 33, 0)
                    ],
                    "time_step": 60
                }
            },
            "vancouver_files": {
                # This is defined by specifying path to the first file.
                # Command-line will typically be invoked like this.

                # All expected data should be the same as in vancouver_archive
                "params": {
                    "system": "evo",
                    "starting_filename": "/home/jarek/evo-vancouver/vancouver_2015-06-19/vancouver_2015-06-19--00-00",
                    "starting_time": None,
                    "ending_time": None,
                    "time_step": 60
                },
                "expected_stats": {
                    "total vehicles": 238,
                    "total trips": 1333,
                    "starting time": datetime(2015, 6, 19, 0, 0, 0),
                    "ending time": datetime(2015, 6, 19, 23, 59, 0),
                    "time elapsed seconds": 86340.0,
                    "utilization ratio": 0.1325850702,
                    "trips per car per day quartile 25": 3.002084781,
                    "distance per trip quartile 25": 0.1563771331,
                    "duration per trip quartile 75": 37.0,
                    "weird trip count": 37
                },
                "expected_dataframes": {
                    0: {
                        "index": 0,
                        "turn": "2015-06-19T00:00:00",
                        "len_trips": 0,
                        "len_cars": 162
                    },
                    -1: {
                        "index": 1439,
                        "turn": "2015-06-19T23:59:00",
                        "len_cars": 165
                    }
                },
                "expected_metadata": {
                    "city": "vancouver",
                    "system": "evo",
                    "starting_time": datetime(2015, 6, 19, 0, 0, 0),
                    "ending_time": datetime(2015, 6, 19, 23, 59, 0),
                    "missing": [
                        datetime(2015, 6, 19, 6, 46, 0),
                        datetime(2015, 6, 19, 7, 9, 0),
                        datetime(2015, 6, 19, 17, 33, 0)
                    ],
                    "time_step": 60
                }
            }
    }

    @classmethod
    def setUpClass(cls):
        # read in data just once
        cls.results = {}

        for dataset_name in cls.datasets:
            params = cls.datasets[dataset_name]["params"]

            result_dict = normalize.batch_load_data(**params)

            cls.results[dataset_name] = result_dict

    def test_stats_for_sample_datasets(self):
        for dataset_name in self.datasets:
            exp_stats = self.datasets[dataset_name]["expected_stats"]

            stats = process_stats.stats_dict(self.results[dataset_name])

            # for consistent significant figures between py2 and py3
            stats = process_stats.repr_floats(stats)
            exp_stats = process_stats.repr_floats(exp_stats)

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
            data_frames = list(generate.build_data_frames(self.results[dataset_name]))

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

    def test_metadata_for_sample_datasets(self):
        for dataset_name in self.datasets:
            if 'expected_metadata' in self.datasets[dataset_name]:
                exp_metadata = self.datasets[dataset_name]["expected_metadata"]

                got_metadata = self.results[dataset_name]["metadata"]

                for category in exp_metadata:
                    self.assertEqual(exp_metadata[category], got_metadata[category],
                                     "{name} {cat}: expected {exp}, got {got}".format(
                                         name=dataset_name, cat=category,
                                         exp=exp_metadata[category], got=got_metadata[category]))


class MergeTest(unittest.TestCase):
    # Like StatsTest, also hardcoded to a dataset I have.

    def test_merge(self):
        filenames = [
            'columbus_2015-06-01.json',
            'columbus_2015-06-02.json',
            'columbus_2015-06-03.json'
            ]
        filepaths = ['/home/jarek/car2go-columbus/' + name for name in filenames]

        merged_dict = merge.merge_all_files(filepaths)

        self.assertEqual(merged_dict['metadata']['starting_time'], datetime(2015, 6, 1, 0, 0))
        self.assertEqual(merged_dict['metadata']['ending_time'], datetime(2015, 6, 3, 23, 59))
        self.assertEqual(len(merged_dict['metadata']['missing']), 3)

        # some test cars that had non-trivial trip history...
        test_vin = 'WMEEJ3BA5EK736813'
        test_vin2 = 'WMEEJ3BAXEK733745'
        test_vin3 = 'WMEEJ3BA3EK732887'

        self.assertEqual(merged_dict['unstarted_trips'][test_vin]['ending_time'], datetime(2015, 6, 1, 0, 0))
        self.assertEqual(merged_dict['unstarted_trips'][test_vin]['to'], [39.95781, -82.9975])
        self.assertEqual(merged_dict['unfinished_parkings'][test_vin]['starting_time'], datetime(2015, 6, 3, 18, 13))
        self.assertEqual(merged_dict['unfinished_parkings'][test_vin]['coords'], [40.05838, -83.00955])
        self.assertTrue(test_vin not in merged_dict['unfinished_trips'])
        self.assertEqual(len(merged_dict['finished_parkings'][test_vin]), 12)
        self.assertEqual(len(merged_dict['finished_trips'][test_vin]), 12)

        self.assertEqual(len(merged_dict['finished_parkings'][test_vin2]),
                         len(merged_dict['finished_trips'][test_vin2]))
        self.assertEqual(len(merged_dict['finished_parkings'][test_vin3]),
                         len(merged_dict['finished_trips'][test_vin3]))


class IntegrationTest(unittest.TestCase):
    # Like StatsTest, also hardcoded to a dataset I have.

    def test_merge_pipeline(self):
        # comprehensive test using command-line interfaces:
        # - normalize.py three files in a row, directing output to JSON files
        # - merge.py the three JSON files, directing output to PIPE
        # - process.py the output of the PIPE to get usage stats
        # - check a few of the stats values to make sure they're the expected numbers for the dataset

        # note, this will always use python3 to run the scripts even if tests.py
        # is ran with python2 - it uses the hashbang in the scripts which is py3

        data_dir = '/home/jarek/car2go-columbus'
        script_dir = os.path.dirname(os.path.abspath(__file__)) + '/scripts'

        data_dir_part_1 = '/home/jarek/'
        data_dir_part_2 = 'car2go-columbus/'

        Popen([os.path.join(script_dir, 'normalize.py'), 'car2go', 'columbus_2015-06-01.tgz'],
              cwd=data_dir,
              stdout=open(os.path.join(data_dir, 'columbus_2015-06-01.json'), 'w')).wait()
        Popen([os.path.join(script_dir, 'normalize.py'), 'car2go', 'columbus_2015-06-02.tgz'],
              cwd=data_dir,
              stdout=open(os.path.join(data_dir, 'columbus_2015-06-02.json'), 'w')).wait()
        # test call using a directory name to make sure this is being parsed properly
        Popen([os.path.join(script_dir, 'normalize.py'), 'car2go', data_dir_part_2 + 'columbus_2015-06-03.tgz'],
              cwd=data_dir_part_1,
              stdout=open(os.path.join(data_dir, 'columbus_2015-06-03.json'), 'w')).wait()

        p1 = Popen([os.path.join(script_dir, 'merge.py'),
                    'columbus_2015-06-01.json', 'columbus_2015-06-02.json', 'columbus_2015-06-03.json'],
                   cwd=data_dir,
                   stdout=PIPE)
        p2 = Popen([os.path.join(script_dir, 'stats.py')],
                   cwd=data_dir,
                   stdin=p1.stdout,
                   stdout=PIPE)
        p1.stdout.close()  # Allow m1 to receive a SIGPIPE if p2 exits.

        stats_file = p2.communicate()[0].strip().decode('utf-8')

        stats_file_path = os.path.join(data_dir, stats_file)
        
        if not os.path.isfile(stats_file_path):
            self.fail("stats file not generated by stats.py")

        with open(os.path.join(data_dir, stats_file)) as f:
            reader = csv.reader(f)
            title_row = next(reader)
            data_row = next(reader)

            def get_data(category):
                index = title_row.index(category)
                return data_row[index]

            # they're strings because everything in CSV is a string by default I think
            self.assertEqual(get_data('utilization ratio'), '0.06061195898')
            self.assertEqual(get_data('trips per car mean'), '8.677966102')
            self.assertEqual(get_data('distance per trip quartile 75'), '3.362357622')


class HelperFunctionsTest(unittest.TestCase):
    def test_is_latlng_in_bounds(self):
        VALUES = {
            'vancouver': [49.25199,-123.06672],
            'toronto': [43.66666,-79.33333],
            'wien': [48.2,16.3667],
            'buenosaires': [-34.3,-58.5]
        }

        # test northern and western hemisphere
        self.assertTrue(process_graph.is_latlng_in_bounds(CITIES['vancouver'],
                                                          VALUES['vancouver']))
        self.assertTrue(process_graph.is_latlng_in_bounds(CITIES['toronto'],
                                                          VALUES['toronto']))

        # test northern and eastern hemisphere
        self.assertTrue(process_graph.is_latlng_in_bounds(CITIES['wien'],
                                                          VALUES['wien']))

        # TODO: test correctness of calculation for southern hemisphere
        #self.assertTrue(process_graph.is_latlng_in_bounds(city.CITIES, 'buenosaires',
        #                                                  VALUES['buenosaires']))

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
