# coding=utf-8

from collections import Counter, OrderedDict
from datetime import timedelta
import csv
import numpy as np


def write_csv(f, items):
    """
    :type items: list[OrderedDict]
    """

    if len(items) == 0:
        # nothing to write
        return f

    fieldnames = items[0].keys()  # this works as expected because we use OrderedDicts
    writer = csv.DictWriter(f, fieldnames)

    writer.writeheader()
    for item in items:
        writer.writerow(item)

    return f


def write_csv_to_file(output_file, items):
    """
    :type items: list[OrderedDict]
    """

    with open(output_file, 'w') as f:
        write_csv(f, items)


def is_trip_weird(trip):
    # TODO: these criteria are fairly car2go specific. They need to be tested on other systems.

    # TODO: car2go appears to have a significant peak at 32 and 33 minute durations, likely
    # from lapsed reservations - try to filter those.
    # Check directly - and try to guess if it's a lapsed reservation (fuel use?
    # but check similar duration trips to see if their fuel use isn't usually 0 either)

    if trip['duration'] < 4*60 and trip['distance'] <= 0.01 and trip['fuel_use'] > -2:
        # trips under 4 minutes and under 10 metres are likely to be errors
        return True
    elif trip['duration'] == 1*60 and trip['distance'] <= 0.05 and trip['fuel_use'] > -2:
        # trips exactly 1 minute along and under 50 metres are likely to be errors
        return True

    return False


def stats_dict(data_dict):
    starting_time = data_dict['metadata']['starting_time']
    ending_time = data_dict['metadata']['ending_time']

    all_trips = [trip for vin in data_dict['finished_trips'] for trip in data_dict['finished_trips'][vin]]

    all_known_vins = set()
    all_known_vins.update(data_dict['unfinished_trips'].keys())
    all_known_vins.update(data_dict['finished_trips'].keys())
    all_known_vins.update(data_dict['unfinished_parkings'].keys())
    all_known_vins.update(data_dict['finished_parkings'].keys())
    all_known_vins.update(data_dict['unstarted_trips'].keys())

    def stats_for_collection(collection, collection_binned, days=1.0, over=False, under=False, most_common_count=10):
        """
        :type over: list
        :type under: list
        """

        def dataset_count_over(trips, thresholds, is_over=True):
            results = []
            for threshold in thresholds:
                if is_over:
                    trip_count = len([x for x in trips if x > threshold])
                else:
                    trip_count = len([x for x in trips if x < threshold])

                results.append((threshold, trip_count))

            return results

        def quartiles(quartiles_collection, quartiles_days):
            quartiles_dict = {}
            for i in range(0, 101, 25):
                quartiles_dict[i] = np.percentile(quartiles_collection, i) / quartiles_days
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
            days *= 1.0  # make sure it's a decimal
            result['mean per day'] = result['mean'] / days
            quartiles_per_day = quartiles(collection, days)
            result['median per day'] = quartiles_per_day[50]
            result['quartiles per day'] = quartiles_per_day

        if over and result['count all'] > 0:
            result['thresholds over'] = dataset_count_over(collection, over)

        if under and result['count all'] > 0:
            result['thresholds under'] = dataset_count_over(collection, under, is_over=False)

        return result

    def format_stats(name, input_data):
        """
        Edit the stats dictionary slightly, formatting data to have less dicts/tuples
        and more strings so it is easier to export.
        Also prefix all keys with "name"
        :param input_data: if 'thresholds over' or 'thresholds under' keys are included,
        'count all' key must also be included
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
        if is_trip_weird(trip):
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

    time_missing_seconds = len(data_dict['metadata']['missing']) * data_dict['metadata']['time_step']
    time_missing_ratio = time_missing_seconds * 1.0 / time_elapsed_seconds

    trips_per_car = list(trip_counts_by_vin.values())

    stats = OrderedDict()
    stats['starting time'] = starting_time
    stats['ending time'] = ending_time

    stats['missing data ratio'] = time_missing_ratio

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
                                                   over=[2*60, 5*60, 10*60])))

    parking_durations = duration(trip for vin in data_dict['finished_trips']
                                 for trip in data_dict['finished_trips'][vin])
    stats.update(format_stats('duration per parking',
                              stats_for_collection(parking_durations,
                                                   collection_round(parking_durations, 5),
                                                   over=[2*60, 6*60, 12*60, 36*60])))
    # TODO: It might be more informative to calculate
    # (total length of parkings over 2 hours) / (total length of all parkings) instead of
    # (number of parkings over 2 hours) / (number of all parkings) as we're doing now
    # - or at least in addition to

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


def stats_slice(data_dict, from_time, to_time):
    """
    Get a slice of data_dict containing only activity between
    from_time and to_time.

    This is intended for stats purposes, to split larger datasets to get
    use stats by day or week.

    Trips that straddle the cut-off datetimes are truncated to start/end
    on from_time and to_time in attempt to make utilization ratio calculation
    more accurate. This makes trip duration data less accurate.

    This is necessarily slightly imprecise, for instance cut-off
    parts of trips can be getting classified as mini weird trips.
    However, accuracy for utilization ratio is well under 1%.
    """

    result_dict = {
        'finished_trips': {},
        'finished_parkings': {},
        'unfinished_trips': {},
        'unfinished_parkings': {},
        'unstarted_trips': {},
        'metadata': dict.copy(data_dict['metadata'])
    }

    for vin in data_dict['finished_trips']:
        # first do the rough filtering
        # use dict.copy to avoid changing trip durations in the passed-by-reference data_dict
        trips = [dict.copy(trip) for trip in data_dict['finished_trips'][vin]
                 # normal trips, within the day
                 if (from_time <= trip['start']['time'] <= trip['end']['time'] <= to_time)

                 # trips spanning starting_time
                 or (trip['start']['time'] < from_time < trip['end']['time'] < to_time)

                 # trips spanning starting_time
                 or (from_time < trip['start']['time'] < to_time < trip['end']['time'])

                 # trips spanning whole day from from_time to to_time
                 or (trip['start']['time'] < from_time and trip['end']['time'] > to_time)]

        # then trim off ends of trips that straddle dataset borders (either from_time
        # or to_time).
        # this will hit on accuracy of trip duration statistics, but improve
        # accuracy of utilization ratio calculation.
        # need to only look at first_trip and last_trip in the newly filtered list
        # because by definition only one trip each will straddle from_time and to_time.
        if len(trips):
            first_trip = trips[0]
            if first_trip['start']['time'] < from_time:
                first_trip['start']['time'] = from_time
                first_trip['duration'] = (first_trip['end']['time'] - from_time).total_seconds()
                # not recalculating speed since it'll be pretty meaningless on the changed duration

            last_trip = trips[-1]
            if last_trip['end']['time'] > to_time:
                last_trip['end']['time'] = to_time
                last_trip['duration'] = (to_time - last_trip['start']['time']).total_seconds()

        result_dict['finished_trips'][vin] = trips

    # filter out cars with no trips
    result_dict['finished_trips'] = {vin: trips for vin, trips in result_dict['finished_trips'].items()
                                     if len(trips) > 0}

    for vin in data_dict['finished_parkings']:
        # first do the rough filtering
        # see comments for finished_trips filter above for reasoning
        parks = [dict.copy(park) for park in data_dict['finished_parkings'][vin]
                 if (from_time <= park['starting_time'] <= park['ending_time'] <= to_time)
                 or (park['starting_time'] < from_time < park['ending_time'] < to_time)
                 or (from_time < park['starting_time'] < to_time < park['ending_time'])
                 or (park['starting_time'] < from_time and park['ending_time'] > to_time)]

        # trim off ends as for finished_trips
        if len(parks):
            first_park = parks[0]
            if first_park['starting_time'] < from_time:
                first_park['starting_time'] = from_time
                first_park['duration'] = (first_park['ending_time'] - from_time).total_seconds()

            last_park = parks[-1]
            if last_park['ending_time'] > to_time:
                last_park['ending_time'] = to_time
                last_park['duration'] = (to_time - last_park['starting_time']).total_seconds()

        result_dict['finished_parkings'][vin] = parks

    # filter out cars with no parkings
    result_dict['finished_parkings'] = {vin: parkings for vin, parkings in result_dict['finished_parkings'].items()
                                        if len(parkings) > 0}

    # TODO: should we add unfinished into finished, trimming them?
    # to_time is already non-inclusive (e.g. from_time being 04:00, to_time will be 03:59),
    # so we use less-than-or-equal, from_time <= data <= to_time
    unfi_parkings = data_dict['unfinished_parkings']
    result_dict['unfinished_parkings'] = {vin: unfi_parkings[vin] for vin in unfi_parkings
                                          if from_time <= unfi_parkings[vin]['starting_time'] <= to_time}

    unfi_trips = data_dict['unfinished_trips']
    result_dict['unfinished_trips'] = {vin: unfi_trips[vin] for vin in unfi_trips
                                       if from_time <= unfi_trips[vin]['start']['time'] <= to_time}

    unst_trips = data_dict['unstarted_trips']
    result_dict['unstarted_trips'] = {vin: unst_trips[vin] for vin in unst_trips
                                      if from_time <= unst_trips[vin]['end']['time'] <= to_time}

    # Now we just need to adjust metadata
    result_dict['metadata']['starting_time'] = from_time
    result_dict['metadata']['ending_time'] = to_time

    # adjust missing data points
    # note that the list comp implicitly does a copy of the `missing` list, which is good,
    # because we need the original missing list for next iterations
    result_dict['metadata']['missing'] = [missing_datetime for missing_datetime
                                          in data_dict['metadata']['missing']
                                          if from_time <= missing_datetime < to_time]

    # TODO: there is a bug here somewhere:
    # analysing the same time period from two differently-cut datasets gives different results.
    # e.g., a dataset from 2015-07-20 to 2015-08-09 and another dataset from 2015-08-01 to 2015-08-19
    # both contain a period from 2015-08-01 to 2015-08-08 but the resulting statistics
    # are slightly different. This is bad.

    # I think I should rewrite how the unstarted/unfinished trips are treated in general.
    # Rather than trimming ends off but keeping the trips in trips dicts, should convert them
    # to unstarted/unfinished trips instead.

    # TODO: need to create tests after "correct" logic is finalized

    # TODO: split this code into a "split.py" or "splice.py" to complement merge.py

    # TODO: make a basic visualiser? using the slice function and output into json,
    # and a HTML/js to take in that json and display it in little lines with tooltips identifying cars
    # Would be useful for debugging - and also for future visualisations

    return result_dict


def repr_floats(result):
    # Force floats to formatted strings to avoid differences in precision
    # between Python 2 and Python 3, and between separate runs under Python 3.
    # Floats have to be stringified for CSV output anyway, and doing so now
    # lets us do it consistently.
    # Use 10 significant digits as this is more than enough for stats
    # while well less than level where float representation issues crop up.

    for key in result:
        if isinstance(result[key], float):
            result[key] = format(result[key], '.10g')

    return result


def stats(data_dict, output_file, tz_offset):
    # First, get data for whole data_dict dataset

    result = repr_floats(stats_dict(data_dict))

    all_results = [result]

    # Next, create slices of data_dict containing a day's and week's
    # (where available) data to get more detailed statistics automatically

    time_step = timedelta(seconds=data_dict['metadata']['time_step'])
    slice_time = data_dict['metadata']['starting_time'] - time_step

    # Use tz_offset (from process.py's -tz param) to offset start time for data slice.
    # Times in data_dict are expected to be UTC so this can be used to correct for timezone.
    slice_time -= timedelta(hours=tz_offset)

    # Use 4.a.m local time for better logical split of "days"
    slice_time += timedelta(hours=4)

    while slice_time <= data_dict['metadata']['ending_time']:
        one_day_from_time = slice_time - timedelta(days=1) + time_step

        # Note: trips_per_car and similar stats will be inaccurate if cars are added or removed
        # during the data period, as the highest car count during the data period will be used
        # for all slices
        if one_day_from_time >= data_dict['metadata']['starting_time']:
            sliced_dict = stats_slice(data_dict, one_day_from_time, slice_time)

            result = repr_floats(stats_dict(sliced_dict))

            all_results.append(result)

        seven_days_from_time = slice_time - timedelta(days=7) + time_step
        if seven_days_from_time >= data_dict['metadata']['starting_time']:
            sliced_dict = stats_slice(data_dict, seven_days_from_time, slice_time)

            result = repr_floats(stats_dict(sliced_dict))

            all_results.append(result)

        slice_time += timedelta(days=1)

    write_csv_to_file(output_file, all_results)
