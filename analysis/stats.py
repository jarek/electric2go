#!/usr/bin/env python2
# coding=utf-8

from collections import Counter, OrderedDict
import numpy as np
import scipy.stats as sps


# TODO: these functions should create CSV rather than print results

def trace_vehicle(trips, criterion):
    def format_trip(trip):
        result  = 'start: %s at %f,%f' % \
            (trip['starting_time'], trip['from'][0], trip['from'][1])
        result += ', end: %s at %f,%f' % \
            (trip['ending_time'], trip['to'][0], trip['to'][1])
        result += '\n\tduration: %d minutes' % (trip['duration'] / 60)
        result += '\tdistance: %0.2f km' % (trip['distance'])
        result += '\tfuel: starting %d%%, ending %d%%' % \
            (trip['starting_fuel'], trip['ending_fuel'])

        if trip['ending_fuel'] > trip['starting_fuel']:
            result += ' - refueled'

        return result

    lines = []

    vin = trips[0]['vin'] if len(trips) else 'none'

    if criterion == 'most_trips':
        lines.append('vehicle with most trips is %s with %d trips' %
                     (vin, len(trips)))
    elif criterion == 'most_distance':
        lines.append('vehicle with highest distance travelled is %s with %0.3f km' %
                     (vin, sum(t['distance'] for t in trips)))
    elif criterion == 'most_duration':
        duration = sum(t['duration'] for t in trips)/60
        lines.append('vehicle with highest trip duration is %s with %d minutes (%0.2f hours)' %
                     (vin, duration, duration/60))

    lines.append('trips for vehicle %s: (count %d)' % (vin, len(trips)))
    for trip in trips:
        lines.append(format_trip(trip))

    return '\n'.join(lines)

def print_stats(all_trips, all_known_vins, starting_time, ending_time,
    weird_trip_distance_cutoff = 0.05, weird_trip_time_cutoff = 5,
    # time cutoff should be 2 for 1 minute step data
    weird_trip_fuel_cutoff = 1):

    def dataset_count_over(trips, thresholds, sorting_lambda=False):
        results = []
        for threshold in thresholds:
            if not sorting_lambda:
                trip_count = sum(1 for x in trips if x > threshold)
            else:
                trip_count = sum(1 for x in trips if sorting_lambda(x, threshold))

            results.append((threshold, trip_count))

        return results

    def trip_breakdown(trips, sorting_bins = [120, 300, 600],
        sorting_lambda = False, label = False):
        # uses stats['total_trips'] defined before calling this subfunction
        lines = []
        for i in sorting_bins:
            if not sorting_lambda:
                trip_count = sum(1 for x in trips if x > i)
            else:
                trip_count = sum(1 for x in trips if sorting_lambda(x, i))

            trip_percent = trip_count * 1.0 / stats['total_trips']

            if not label:
                line = 'trips over %d hours: %s' % \
                    (i/60, trip_count_stats(trip_count))
            else:
                line = label(i, trip_count_stats(trip_count))
            lines.append(line)
        return '\n'.join(lines)

    def trip_count_stats(trip_count):
        # uses time_days and stats['total_trips'] defined 
        # before calling this subfunction

        if abs(time_days-1.0) < 0.01:
            # don't calculate trips per day if value is within 1% of a day
            # that's close enough that the differences won't matter in practice
            return '%d (%0.4f of all trips)' % \
                (trip_count, trip_count * 1.0 / stats['total_trips'])
        else:
            return '%d (%0.2f per day; %0.4f of all trips)' % \
                (trip_count, trip_count/time_days, 
                trip_count * 1.0 / stats['total_trips'])

    def quartiles(collection, days=1.0):
        result = {}
        for i in range(0, 101, 25):
            result[i] = sps.scoreatpercentile(collection, i) / days
        return result

    def get_stats(collection, collection_binned, days=1, over=False, most_common_count=10):
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

        if over:
            result['thresholds'] = dataset_count_over(collection, over)

        return result

    def format_stats(name, input_data):
        result = OrderedDict()

        # format quartiles
        if 'quartiles' in input_data:
            for threshold, amount in input_data['quartiles'].items():
                input_data['quartile %d' % threshold] = amount
            del input_data['quartiles']

        if 'quartiles per day' in input_data:
            for threshold, amount in input_data['quartiles per day'].items():
                input_data['per day quartile %d' % threshold] = amount
            del input_data['quartiles per day']

        # format thresholds
        if 'thresholds' in input_data:
            for threshold, count_over in input_data['thresholds']:
                input_data['over %d ratio' % threshold] = count_over * 1.0 / input_data['count all']
            del input_data['thresholds']

        # prefix with name
        for key, value in input_data.items():
            result['%s %s' % (name, key)] = value

        return result

    def round_to(value, round_to):
        return round_to*int(value*(1.0/round_to))

    data = {'total_trips': 0, 'trips': [],
            'total_distance': 0, 'distances': [], 'distance_bins': [],
            'total_duration': 0, 'durations': [], 'duration_bins': []}
    weird = []
    suspected_round_trip = []
    refueled = []
    trip_counts_by_vin = {}
    for trip in all_trips:
        vin = trip['vin']
        trip_counts_by_vin[vin] = trip_counts_by_vin.get(vin, 0) + 1

        if trip['distance'] <= weird_trip_distance_cutoff:
            suspected_round_trip.append(trip)
            test_duration = weird_trip_time_cutoff * 60 # min to sec
            #print trip
            if trip['duration'] <= test_duration and \
                trip['fuel_use'] <= weird_trip_fuel_cutoff:
                # do not count this trip... it's an anomaly
                #print 'weird'
                weird.append(trip)
                trip_counts_by_vin[vin] = trip_counts_by_vin[vin] - 1
                continue

        data['total_duration'] += trip['duration']/60
        data['durations'].append(trip['duration']/60)

        # bin to nearest five minutes (if it isn't already)
        data['duration_bins'].append(round_to(trip['duration']/60, 5))

        data['total_distance'] += trip['distance']
        data['distances'].append(trip['distance'])

        # bin to nearest 0.5 km
        data['distance_bins'].append(round_to(trip['distance'], 0.5))

        if 'starting_fuel' in trip:
            if trip['ending_fuel'] > trip['starting_fuel']:
                refueled.append(trip)

    for vin in all_known_vins:
        if vin not in trip_counts_by_vin:
            trip_counts_by_vin[vin] = 0

    # subtracting time_step below to get last file actually processed
    time_elapsed = ending_time - starting_time
    time_elapsed_seconds = time_elapsed.total_seconds()
    time_days = time_elapsed_seconds * 1.0 / (24*60*60)

    data['trips'] = trip_counts_by_vin.values()

    stats = OrderedDict()
    stats['total_vehicles'] = len(trip_counts_by_vin)
    stats['total_trips'] = len(all_trips) - len(weird)
    stats['total_trips per day'] = stats['total_trips'] / time_days

    stats['time_elapsed_seconds'] = time_elapsed_seconds
    stats['time_elapsed_days'] = time_days

    stats['utilization_ratio'] = data['total_duration'] / stats['total_vehicles'] / (time_elapsed_seconds/60)

    stats.update(format_stats('trips per car',
                              get_stats(data['trips'], data['trips'], time_days)))

    stats.update(format_stats('distance per trip',
                              get_stats(data['distances'], data['distance_bins'], over=[5, 10])))

    stats.update(format_stats('duration per trip',
                              get_stats(data['durations'], data['duration_bins'], over=[120, 300, 600])))

    for key, value in stats.items():
        print '%s : %s' % (key, value)

    # TODO: clean up code detecting weird trips and generating statistics from those as well.
    # TODO: return a dict suited for saving to CSV file rather than printing

    # this is a weirdness with the datasets: 
    # some have lots of short (<50 m, even <10m) trips.
    # e.g., the austin sxsw has about 90 trips per day like that.
    # unfortunately the API doesn't give us mileage, so hard to tell if
    # it was a round trip, or if a car even moved at all.
    # not sure what to do with them yet...
    #weird_backup = weird
    #weird = suspected_round_trip
    durations = list(x['duration']/60 for x in weird)
    distances = list(x['distance'] for x in weird)
    distance_bins = list(int(1000*round_to(x['distance'], 0.005)) 
        for x in weird)
    fuel_uses = list(x['starting_fuel'] - x['ending_fuel'] for x in weird)

    print '\ntrips reported shorter than %d m: %s' % \
        (weird_trip_distance_cutoff * 1000, trip_count_stats(len(weird)))
    print '\ndurations (minutes): mean %0.2f, stdev %0.3f, max %d' % \
        (np.mean(durations), np.std(durations), max(durations))
    print 'most common durations: %s' %Counter(durations).most_common(10)
    print trip_breakdown(durations)
    print '\ndistances (km): mean %0.4f, stdev %0.4f, max %0.2f' % \
        (np.mean(distances), np.std(distances), max(distances))
    print 'most common distances in metres, rounded to nearest 5 m: %s' % \
        Counter(distance_bins).most_common(10)
    print '\nfuel use (in percent capacity): mean %0.2f, stdev %0.3f, max %d' % \
        (np.mean(fuel_uses), np.std(fuel_uses), max(fuel_uses))
    print 'most common fuel uses: %s' % Counter(fuel_uses).most_common(10)
    print trip_breakdown(fuel_uses, sorting_bins = [1, 5, 0],
        sorting_lambda = (lambda x, i: (x > i) if i > 0 else (x < i)),
        label = (lambda fuel, string: 
            'more than %d pp fuel use: %s' % (fuel, string) if (fuel > 0) else
            'refueled: %s' % string))

