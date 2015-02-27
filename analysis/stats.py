#!/usr/bin/env python2
# coding=utf-8

from collections import Counter, OrderedDict
import unicodecsv
from datetime import datetime
import numpy as np
import scipy.stats as sps


def csv_file_name(category):
    return '{date}_{category}.csv'.format(
        date=datetime.now().strftime('%Y%m%d-%H%M%S'),
        category=category)


def write_csv(f, items):
    """
    :type items: list[OrderedDict]
    """

    if len(items) == 0:
        # nothing to write
        return f

    fieldnames = items[0].keys()  # this works as expected because we use OrderedDicts
    writer = unicodecsv.DictWriter(f, fieldnames)

    writer.writeheader()
    for item in items:
        writer.writerow(item)

    return f


def write_csv_to_file(category, items):
    file_name = csv_file_name(category)
    with open(file_name, 'w') as f:
        write_csv(f, items)


def trace_vehicle(trips, criterion):
    def trip_dict(trip):
        result = OrderedDict()

        result['vin'] = trip['vin']
        result['position start lat'] = trip['from'][0]
        result['position start lng'] = trip['from'][1]
        result['position end lat'] = trip['to'][0]
        result['position end lng'] = trip['to'][1]
        result['time start'] = trip['starting_time']
        result['time end'] = trip['ending_time']
        result['fuel start'] = trip['starting_fuel']
        result['fuel end'] = trip['ending_fuel']
        result['distance'] = trip['distance']
        result['duration'] = trip['duration'] / 60
        result['fuel use'] = trip['fuel_use']

        # TODO: starting condition, ending condition. will require changes in process.py

        return result

    formatted_trips = map(trip_dict, trips)
    write_csv_to_file(category='trace-{}'.format(criterion),
                      items=formatted_trips)


def stats_dict(all_trips, all_known_vins, starting_time, ending_time):
    def stats_for_collection(collection, collection_binned, days=1.0, over=False, under=False, most_common_count=10):
        """
        :type over: list
        :type under: list
        """

        def dataset_count_over(trips, thresholds, sorting_lambda=False):
            """
            :type sorting_lambda: function
            """
            results = []
            for threshold in thresholds:
                if not sorting_lambda:
                    trip_count = sum(1 for x in trips if x > threshold)
                else:
                    trip_count = sum(1 for x in trips if sorting_lambda(x, threshold))

                results.append((threshold, trip_count))

            return results

        def quartiles(quartiles_collection, quartiles_days):
            quartiles_dict = {}
            for i in range(0, 101, 25):
                quartiles_dict[i] = sps.scoreatpercentile(quartiles_collection, i) / quartiles_days
            return quartiles_dict

        result = OrderedDict()
        result['count all'] = len(collection)
        result['mean'] = np.mean(collection)
        result['std'] = np.std(collection)
        quartiles_overall = quartiles(collection, 1.0)
        result['median'] = quartiles_overall[50]
        result['quartiles'] = quartiles_overall
        result['most common binned values'] = Counter(collection_binned).most_common(most_common_count)

        if days != 1.0:
            days = days * 1.0  # make sure it's a decimal
            result['mean per day'] = result['mean'] / days
            quartiles_per_day = quartiles(collection, days)
            result['median per day'] = quartiles_per_day[50]
            result['quartiles per day'] = quartiles_per_day

        if over and result['count all'] > 0:
            result['thresholds over'] = dataset_count_over(collection, over)

        if under and result['count all'] > 0:
            result['thresholds under'] = dataset_count_over(collection, under, sorting_lambda=lambda x, thr: x < thr)

        return result

    def format_stats(name, input_data):
        """
        Edit the stats dictionary slightly, formatting data to have less dicts/tuples
        and more strings so it is easier to export.
        Also prefix all keys with "name"
        :param input_data: if 'thresholds over' or 'thresholds under' keys are included, 'count all' key must also be included
        """
        result = OrderedDict()

        # format quartiles
        if 'quartiles' in input_data:
            for threshold, amount in input_data['quartiles'].items():
                input_data['quartile {}'.format(threshold)] = amount
            del input_data['quartiles']

        if 'quartiles per day' in input_data:
            for threshold, amount in input_data['quartiles per day'].items():
                input_data['per day quartile {}'.format(threshold)] = amount
            del input_data['quartiles per day']

        # format thresholds
        if 'thresholds over' in input_data:
            for threshold, count_over in input_data['thresholds over']:
                input_data['over {} ratio'.format(threshold)] = count_over * 1.0 / input_data['count all']
            del input_data['thresholds over']

        if 'thresholds under' in input_data:
            for threshold, count_over in input_data['thresholds under']:
                input_data['under {} ratio'.format(threshold)] = count_over * 1.0 / input_data['count all']
            del input_data['thresholds under']

        # prefix with name
        for input_key, input_value in input_data.items():
            result['%s %s' % (name, input_key)] = input_value

        return result

    def duration(collection):
        return [coll_trip['duration']/60 for coll_trip in collection]

    def distance(collection):
        return [coll_trip['distance'] for coll_trip in collection]

    def fuel(collection):
        return [coll_trip['fuel_use'] for coll_trip in collection]

    def collection_round(collection, round_to):
        return [round_to * int(coll_value * (1.0 / round_to)) for coll_value in collection]

    trips_weird = []
    trips_good = []
    trips_refueled = []
    trip_counts_by_vin = {}
    for trip in all_trips:
        # Find and exclude "weird" trips, that are likely to be system errors caused by things like GPS misreads
        # rather than actual trips.
        # Not all errors will be caught - sometimes it is impossible to tell. Consequently,
        # this operates on a best-effort basis, catching some of the most common and obvious problems.
        # Various "weird" trips like that are somewhat less than 1% of a test dataset (Vancouver, Jan 27 - Feb 3)
        # and the conditions below catch roughly 50-80% of them.
        # TODO: these criteria are fairly car2go specific. They need to be tested on other systems.
        if trip['duration'] < 4*60 and trip['distance'] <= 0.01 and trip['fuel_use'] > -2:
            # trips under 4 minutes and under 10 metres are likely to be errors
            trips_weird.append(trip)
        elif trip['duration'] == 1*60 and trip['distance'] <= 0.05 and trip['fuel_use'] > -2:
            # trips exactly 1 minute along and under 50 metres are likely to be errors
            trips_weird.append(trip)
        else:
            trips_good.append(trip)

            trip_counts_by_vin[trip['vin']] = trip_counts_by_vin.get(trip['vin'], 0) + 1

            # TODO: also collect short distance but long duration and/or fuel use - these are likely to be round trips.
            # Some sort of heuristic might have to be developed that establishes ratios of duration/fuel use
            # that make a trip likely a round trip. Complicating matters is the fact that fuel use is quite unreliable.

            if 'fuel_use' in trip and trip['fuel_use'] < 0:
                # collect trips that have included a refuel, for use in stats to be added later
                trips_refueled.append(trip)

    for vin in all_known_vins:
        # fill in trip count for cars with 0 trips, if any
        if vin not in trip_counts_by_vin:
            trip_counts_by_vin[vin] = 0

    time_elapsed_seconds = (ending_time - starting_time).total_seconds()
    time_elapsed_days = time_elapsed_seconds * 1.0 / (24*60*60)

    trips_per_car = trip_counts_by_vin.values()

    stats = OrderedDict()
    stats['total vehicles'] = len(trip_counts_by_vin)
    stats['total trips'] = len(trips_good)
    stats['total trips per day'] = len(trips_good) / time_elapsed_days

    stats['time elapsed seconds'] = time_elapsed_seconds
    stats['time elapsed days'] = time_elapsed_days

    stats['utilization ratio'] = sum(duration(trips_good)) / len(trip_counts_by_vin) / (time_elapsed_seconds/60)

    stats.update(format_stats('trips per car',
                              stats_for_collection(trips_per_car,
                                                   trips_per_car,
                                                   time_elapsed_days)))

    stats.update(format_stats('distance per trip',
                              stats_for_collection(distance(trips_good),
                                                   collection_round(distance(trips_good), 0.5),
                                                   over=[5, 10])))

    stats.update(format_stats('duration per trip',
                              stats_for_collection(duration(trips_good),
                                                   collection_round(duration(trips_good), 5),
                                                   over=[2, 5, 10])))

    stats.update(format_stats('fuel use stats',
                              stats_for_collection(fuel(trips_good),
                                                   fuel(trips_good),
                                                   under=[1, 5],
                                                   over=[1, 5, 10])))

    # get some stats on weird trips as outlined above
    if len(trips_weird) > 0:
        stats['weird trip count'] = len(trips_weird)
        stats['weird trips per day'] = len(trips_weird) * 1.0 / time_elapsed_days
        stats['weird trip ratio'] = len(trips_weird) * 1.0 / len(all_trips)

        stats.update(format_stats('weird trips duration',
                                  stats_for_collection(duration(trips_weird),
                                                       duration(trips_weird))))
        stats.update(format_stats('weird trips distance',
                                  stats_for_collection(distance(trips_weird),
                                                       collection_round(distance(trips_weird), 0.002),
                                                       under=[0.01, 0.02])))

    return stats


def stats(all_trips, all_known_vins, starting_time, ending_time):
    result = stats_dict(all_trips, all_known_vins, starting_time, ending_time)

    write_csv_to_file(category='stats', items=[result])
