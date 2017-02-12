#!/usr/bin/env python3
# coding=utf-8

from __future__ import unicode_literals
import unittest
import os
import numpy as np
import json
import csv
import tempfile
from subprocess import Popen, PIPE
from datetime import datetime, timedelta

from electric2go import current_git_revision, files, download, systems
from electric2go.analysis import normalize, merge, generate
from electric2go.analysis import graph as process_graph
from electric2go.analysis import stats as process_stats

CITIES = systems.get_all_cities("car2go")

# TODO: we need way more tests


class DownloadTest(unittest.TestCase):
    # The system-city pairs to test
    # Optimally we want to test each system here.
    test_cities = [
        ('car2go', 'wien'),  # use Vienna to test non-ASCII handling
        ('evo', 'vancouver'),
        ('drivenow', 'koeln'),
        ('enjoy', 'milano'),
        ('communauto', 'montreal'),
        ('multicity', 'berlin'),
        ('sharengo', 'milano'),
        ('translink', '020')
    ]

    # For systems with several cities, name two different cities
    # so we can check that their API output is not identical.
    test_different_cities = [
        ('car2go', ['wien', 'vancouver']),
        ('drivenow', ['berlin', 'stockholm']),
        ('enjoy', ['milano', 'firenze']),
        ('translink', ['010', '020'])
    ]

    def _assert_api_output_is_valid_json(self, text):
        # could throw exception if JSON is malformed, test if it does
        info = json.loads(text)

        # assert there is something in the object
        self.assertGreater(len(info), 0)

    def test_get_api_output_as_json(self):
        """
        Test that all systems specified successfully return a JSON object.

        NOTE: this currently assumes all systems output JSON.
        This assumption is baked fairly deeply into the project,
        in web_helper.get_electric_cars and
        in analysis.normalize.Electric2goDataArchive
        """
        for city in self.test_cities:
            city_data = systems.get_city_by_name(city[0], city[1])

            text, session = download.download_one_city(city_data)
            session.close()

            self._assert_api_output_is_valid_json(text)

    def test_output_not_identical_for_different_cities(self):
        """
        For selected systems, request information for two different cities
        supported and make sure they're not the same.

        Checks for silly errors like always returning data for the same city,
        no matter which city is requested.
        """
        for city in self.test_different_cities:
            first_city = systems.get_city_by_name(city[0], city[1][0])
            first_text, session = download.download_one_city(first_city)

            second_city = systems.get_city_by_name(city[0], city[1][1])
            second_text, session = download.download_one_city(second_city,
                                                              session=session)
            session.close()

            self.assertNotEqual(first_city, second_city)

    def test_download(self):
        """
        Test that downloading the data results in physical file being created
        for all systems specified.
        """
        for city in self.test_cities:
            city_data = systems.get_city_by_name(city[0], city[1])

            t, failures = download.save(city[0], city[1], should_archive=True)

            self.assertEqual(len(failures), 0)

            file_absolute = files.get_file_path(city_data, t)
            file_current = files.get_current_file_path(city_data)

            self.assertTrue(os.path.exists(file_absolute))
            self.assertTrue(os.path.exists(file_current))

    def test_download_create_dir(self):
        """
        Tests that downloader will attempt to create data directories
        if they don't exist.
        """
        import shutil

        city_data = {'system': 'sharengo', 'name': 'milano'}
        data_dir = files.get_data_dir(city_data)

        # delete if already exists
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)

        # download
        t, failures = download.save(city_data['system'], city_data['name'], False)
        file_current = files.get_current_file_path(city_data)

        # test it was downloaded
        self.assertEqual(len(failures), 0)
        self.assertTrue(os.path.exists(file_current))

    def test_cache(self):
        """
        Tests that repeated requests to get data for a given system
        and city result in cached data being returned.
        """
        for city in self.test_cities:
            city_data = systems.get_city_by_name(city[0], city[1])

            # warm up the cache
            _, _ = download.save(city[0], city[1], should_archive=False)

            text, cache = download.get_current(city_data, max_cache_age=30)

            # check we've gotten a cached file
            self.assertGreater(cache, 0)

            self._assert_api_output_is_valid_json(text)


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
                    "fuel use stats mean": -0.742084053,
                    "fuel use stats over 5 ratio": 0.04663212435,
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
                    "fuel use stats mean": 0.3960345704,
                    "fuel use stats std": 6.485464921,
                    "fuel use stats under 5 ratio": 0.8698525674,
                    "weird trip count": 103
                },
                "expected_dataframes": {
                    0: {
                        "turn": "2015-05-16T11:00:00",
                        "len_trips": 0
                    },
                    250: {
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
                    "fuel use stats mean": -0.4366091523,
                    "fuel use stats under 1 ratio": 0.647411853,
                    "weird trip count": 37
                },
                "expected_dataframes": {
                    0: {
                        "turn": "2015-06-19T00:00:00",
                        "len_trips": 0,
                        "len_cars": 162
                    },
                    -1: {
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
                    "fuel use stats mean": -0.4366091523,
                    "fuel use stats under 1 ratio": 0.647411853,
                    "weird trip count": 37
                },
                "expected_dataframes": {
                    0: {
                        "turn": "2015-06-19T00:00:00",
                        "len_trips": 0,
                        "len_cars": 162
                    },
                    -1: {
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
            "vancouver_zipfile": {
                # test normalizing files contained in a ZIP file
                "params": {
                    "system": "car2go",
                    "starting_filename": "/home/jarek/car2go-vancouver/vancouver_2015-01.zip",
                    "starting_time": datetime(2015, 1, 4, 0, 0, 0),
                    "ending_time": datetime(2015, 1, 4, 23, 59, 0),
                    "time_step": 60
                },
                "expected_stats": {
                    "total vehicles": 673,
                    "missing data ratio": 0.0,
                    "trips per car quartile 75": 14.0,
                    "distance per trip median": 1.76005701,
                    "duration per trip quartile 25": 15.0,
                    "fuel use stats std": 9.581810626,
                    "fuel use stats over 10 ratio": 0.003516624041,
                    "weird trip ratio": 0.04648681603
                },
                "expected_dataframes": {
                    0: {
                        "turn": "2015-01-04T00:00:00",
                        "len_trips": 0,
                        "len_cars": 563
                    },
                    720: {
                        "turn": "2015-01-04T12:00:00",
                        "len_cars": 444
                    },
                    -1: {
                        "turn": "2015-01-04T23:59:00",
                        "len_cars": 578
                    }
                },
                "expected_metadata": {
                    "time_step": 60,
                    "starting_time": datetime(2015, 1, 4, 0, 0, 0),
                    "ending_time": datetime(2015, 1, 4, 23, 59, 0),
                    "city": "vancouver",
                    "system": "car2go",
                    "missing": []
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

    def test_metadata(self):
        """
        Even though this doesn't test any of the stats,
        it's piggybacked in this test as it verifies
        the dynamic metadata (not dataset-dependent).
        """
        for key in self.results:
            metadata = self.results[key]['metadata']

            # Test generation date, give it 5 minutes of leeway
            # to avoid spurious test failures around midnight.
            now = datetime.utcnow()
            then = metadata['processing_started']
            self.assertLess(now - then, timedelta(minutes=5))

            # Test git revision: verify 'electric2go_revision' is not empty,
            # and verify it's the same as what the module's returns.
            # The latter is a bit pointless, though no more pointless than
            # reimplementing `git rev-parse HEAD` in the test...
            # Verified experimentally that self.assertTrue('') and
            # self.assertTrue(None) fails on pythons 2.7.8 and 3.4.2.
            self.assertTrue(metadata['electric2go_revision'])
            self.assertEqual(metadata['electric2go_revision'],
                             current_git_revision())

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
                if 'turn' in exp_frame:
                    self.assertEqual(exp_frame['turn'], data_frames[i][0].isoformat(),
                                     "{name} {frame} turn: expected {exp}, got {got}".format(
                                         name=dataset_name, frame=i,
                                         exp=exp_frame['turn'], got=data_frames[i][0].isoformat()))
                if 'len_cars' in exp_frame:
                    self.assertEqual(exp_frame['len_cars'], len(data_frames[i][1]),
                                     "{name} {frame} len_cars: expected {exp}, got {got}".format(
                                         name=dataset_name, frame=i,
                                         exp=exp_frame['len_cars'], got=len(data_frames[i][1])))
                if 'len_trips' in exp_frame:
                    self.assertEqual(exp_frame['len_trips'], len(data_frames[i][2]),
                                     "{name} {frame} len_trips: expected {exp}, got {got}".format(
                                         name=dataset_name, frame=i,
                                         exp=exp_frame['len_trips'], got=len(data_frames[i][2])))

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
        # - stats.py reads the output of the PIPE to get usage stats
        # - check a few of the stats values to make sure they're the expected numbers for the dataset

        # note, this will always use python3 to run the scripts even if tests.py
        # is ran with python2 - it uses the hashbang in the scripts which is py3

        data_dir = '/home/jarek/car2go-columbus'
        script_dir = os.path.dirname(os.path.abspath(__file__)) + '/scripts'

        data_dir_part_1 = '/home/jarek/'
        data_dir_part_2 = 'car2go-columbus/'

        with open(os.path.join(data_dir, 'columbus_2015-06-01.json'), 'w') as outfile:
            Popen([os.path.join(script_dir, 'normalize.py'), 'car2go', 'columbus_2015-06-01.tgz'],
                  cwd=data_dir, stdout=outfile).wait()

        with open(os.path.join(data_dir, 'columbus_2015-06-02.json'), 'w') as outfile:
            Popen([os.path.join(script_dir, 'normalize.py'), 'car2go', 'columbus_2015-06-02.tgz'],
                  cwd=data_dir, stdout=outfile).wait()

        # test call using a directory name to make sure this is being parsed properly
        with open(os.path.join(data_dir, 'columbus_2015-06-03.json'), 'w') as outfile:
            Popen([os.path.join(script_dir, 'normalize.py'), 'car2go', data_dir_part_2 + 'columbus_2015-06-03.tgz'],
                  cwd=data_dir_part_1, stdout=outfile).wait()

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


class GenerateTest(unittest.TestCase):
    # TODO:
    # - Test on more Drivenow cities than just Duesseldorf
    #   (although Duesseldorf looks to contain all types of cars that
    #    Drivenow has, so might not be crucial)
    # - Test on car2go city with electric cars, e.g. Amsterdam,
    #   and on city with a few electric cars (Stuttgart maybe?)
    # - In _compare_system_independent, test in loop over the whole dataset
    #   rather than querying just one timepoint
    # - Verify parking periods longer than a day are handled fine in generator

    @classmethod
    def setUpClass(cls):
        # read in data just once
        # this is 181 data points from midnight to 3:00 every minute
        cls.dataset_info = {
            'start': None,
            'end': datetime(2016, 2, 9, 3, 0),
            'freq': 60
        }
        cls.original_data_source = '/home/jarek/projects/electric2go/vancouver_2016-02-09.tgz'
        cls.original_data = normalize.batch_load_data(
            'car2go',
            cls.original_data_source,
            cls.dataset_info['start'], cls.dataset_info['end'], cls.dataset_info['freq'])

        # Create temporary directory to generate class files into.
        # This will be deleted when class goes out of scope.
        # tempdir must be in cls, otherwise it would be deleted
        # when this function finishes.
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.generated_data_dir = cls.tempdir.name

        # generate and write data to a test file
        generate.write_files(cls.original_data, cls.generated_data_dir)

    def test_stats_equal(self):
        # stats for original data
        first_stats = process_stats.stats_dict(self.original_data)

        # get read the generated data back in
        generated_data = normalize.batch_load_data(
            'car2go',
            os.path.join(self.generated_data_dir, 'vancouver_2016-02-09--00-00'),
            self.dataset_info['start'], self.dataset_info['end'], self.dataset_info['freq'])

        # get stats for data generated from the original data
        second_stats = process_stats.stats_dict(generated_data)

        # test that they are the same
        test_keys = ["total vehicles", "missing data ratio", "trips per car quartile 75",
                     "distance per trip median", "duration per trip quartile 25",
                     "weird trip ratio"]

        for test_key in test_keys:
            self.assertEqual(first_stats[test_key], second_stats[test_key],
                             "{test_key}: expected {exp}, got {got}".format(
                                 test_key=test_key,
                                 exp=first_stats[test_key], got=second_stats[test_key]))

    def test_vehicles_equal_car2go(self):
        # load an original file and a newly generated file, and ensure everything
        # in original file is also in new file

        # depends on the files being generated in setUpClass

        # test that all the files are the same
        # TODO: full test takes too long, look at first 40 minutes for now
        # TODO: I previously saw a test fail at 00:37, so that one would be covered, but of course
        # TODO: it would be better to test the whole set
        self._compare_system_from_to('car2go', 'vancouver',
                                     self.original_data_source,
                                     self.generated_data_dir,
                                     self.original_data['metadata']['starting_time'],
                                     datetime(2016, 2, 9, 0, 40),  # TODO: use self.dataset_info['end']
                                     self.dataset_info['freq'])

    def test_vehicles_equal_drivenow(self):
        system = 'drivenow'
        input_file = '/home/jarek/projects/electric2go/duesseldorf_2016-08-20.tgz'

        # read in data
        start = datetime(2016, 8, 20, 0, 0)
        end = datetime(2016, 8, 20, 3, 0)
        freq = 60

        drivenow_original_data = normalize.batch_load_data(system, input_file, None, end, freq)

        # create temporary directory, will be deleted when context manager exits
        with tempfile.TemporaryDirectory() as generated_data_dir:
            # generate 181 files covering from midnight to 3:00 every minute
            generate.write_files(drivenow_original_data, generated_data_dir)

            # test that all the files are the same
            # TODO: full test takes too long, look at first 15 minutes for now
            # TODO: I previously saw a test fail at 00:11, so that one would be covered, but of course
            # TODO: it would be better to test the whole set
            self._compare_system_from_to(system, 'duesseldorf', input_file, generated_data_dir,
                                         start, datetime(2016, 8, 20, 0, 15), freq)  # TODO: use `end` instead of hardcode

    def _compare_system_from_to(self, system, city, expected_location, actual_location,
                                start_time, end_time, time_step):
        comparison_time = start_time
        while comparison_time <= end_time:
            self._compare_system_independent(system, city, expected_location, actual_location, comparison_time)

            comparison_time += timedelta(seconds=time_step)

    def _compare_system_independent(self, system, city, expected_location, actual_location, comparison_time):
        parser = systems.get_parser(system)

        # Name where files have been generated might be a tempdir name
        # like '/tmp/tmp25l2ba19', while Electric2goDataArchive expects
        # a trailing slash if not a file name - so add a trailing slash.
        actual_location = os.path.join(actual_location, '')

        expected_data_archive = normalize.Electric2goDataArchive(city, expected_location)
        expected_file = expected_data_archive.load_data_point(comparison_time)

        actual_data_archive = normalize.Electric2goDataArchive(city, actual_location)
        actual_file = actual_data_archive.load_data_point(comparison_time)

        # test cars equivalency. we have to do it separately because
        # it comes from API as a list, but we don't store the list order.
        expected_cars = parser.get_cars_dict(expected_file)
        actual_cars = parser.get_cars_dict(actual_file)

        error_msg = 'unequal at {}'.format(comparison_time)

        # the following block is more manual than self.assertEqual but gives
        # more useful error messages
        old_max_diff = self.maxDiff
        self.maxDiff = None
        for vin, car in expected_cars.items():
            self.assertEqual(car, actual_cars[vin], msg=error_msg)
        self.maxDiff = old_max_diff

        # now run self.assertEqual in case I'd somehow missed anything
        # during the manual check
        self.assertEqual(expected_cars, actual_cars, msg=error_msg)

        # test exact equivalency of everything but the cars list
        expected_remainder = parser.get_everything_except_cars(expected_file)
        actual_remainder = parser.get_everything_except_cars(actual_file)
        self.assertEqual(expected_remainder, actual_remainder, msg=error_msg)


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
