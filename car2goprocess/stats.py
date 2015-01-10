#!/usr/bin/env python2
# coding=utf-8

from datetime import timedelta
from collections import Counter
from random import choice
import numpy as np
#import scipy.stats as sps


def trace_vehicle(all_trips_by_vin, provided_vin):
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

    vin = provided_vin
    lines = []

    if vin == 'random':
        vin = choice(list(all_trips_by_vin.keys()))
    elif vin == 'most_trips':
        # pick the vehicle with most trips. in case of tie, pick first one
        vin = max(all_trips_by_vin, key = lambda v: len(all_trips_by_vin[v]))
        lines.append('vehicle with most trips is %s with %d trips' % \
            (vin, len(all_trips_by_vin[vin])))
    elif vin == 'most_distance':
        vin = max(all_trips_by_vin, 
            key = lambda v: sum(t['distance'] for t in all_trips_by_vin[v]))
        lines.append(
            'vehicle with highest distance travelled is %s with %0.3f km' % \
            (vin, sum(t['distance'] for t in all_trips_by_vin[vin])))
    elif vin == 'most_duration':
        vin = max(all_trips_by_vin, 
            key = lambda v: sum(t['duration'] for t in all_trips_by_vin[v]))
        duration = sum(t['duration'] for t in all_trips_by_vin[vin])/60
        lines.append('vehicle with highest trip duration is %s ' \
            'with %d minutes (%0.2f hours)' % (vin, duration, duration/60))

    if not vin in all_trips_by_vin:
        return 'vehicle not found in dataset: %s' % provided_vin

    trips = all_trips_by_vin[vin]
    lines.append('trips for vehicle %s: (count %d)' % (vin, len(trips)))
    for trip in trips:
        lines.append(format_trip(trip))

    return '\n'.join(lines)

def print_stats(all_trips, last_data_frame, starting_time, t, time_step,
    weird_trip_distance_cutoff = 0.05, weird_trip_time_cutoff = 5,
    # time cutoff should be 2 for 1 minute step data
    weird_trip_fuel_cutoff = 1):
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

    def quartiles(data):
        result = {}
        for i in range(5):
            pass
            #result[(i*25)] = sps.scoreatpercentile(data, i*25)
        return result

    def format_quartiles(data, format = '%0.3f'):
        result = ''
        data = quartiles(data)
        for percent in data:
            result += '\t%d\t' % percent
            result += format % data[percent]
            result += '\n'
        return result

    def round_to(value, round_to):
        return round_to*int(value*(1.0/round_to))

    stats = {'total_vehicles': 0,
        'total_trips': 0, 'trips': [],
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
            print trip
            if trip['duration'] <= test_duration and \
                trip['fuel_use'] <= weird_trip_fuel_cutoff:
                # do not count this trip... it's an anomaly
                print 'weird'
                weird.append(trip)
                trip_counts_by_vin[vin] = trip_counts_by_vin[vin] - 1
                continue

        stats['total_duration'] += trip['duration']/60
        stats['durations'].append(trip['duration']/60)

        # bin to nearest five minutes (if it isn't already)
        stats['duration_bins'].append(round_to(trip['duration']/60, 5))

        stats['total_distance'] += trip['distance']
        stats['distances'].append(trip['distance'])

        # bin to nearest 0.5 km
        stats['distance_bins'].append(round_to(trip['distance'], 0.5))

        if 'starting_fuel' in trip:
            if trip['ending_fuel'] > trip['starting_fuel']:
                refueled.append(trip)

    for vin in last_data_frame:
        if vin not in trip_counts_by_vin:
            trip_counts_by_vin[vin] = 0

    stats['trips'] = trip_counts_by_vin.values()
    stats['total_vehicles'] = len(trip_counts_by_vin)
    stats['total_trips'] = len(all_trips) - len(weird)

    # subtracting time_step below to get last file actually processed
    time_elapsed = t - timedelta(0, time_step*60) - starting_time
    time_days = time_elapsed.total_seconds() / (24*60*60)
    print 'time elapsed: %s (%0.3f days)' % (time_elapsed, time_days)

    print '\ntotal trips: %d (%0.2f per day), total vehicles: %d' % \
        (stats['total_trips'], stats['total_trips'] * 1.0 / time_days,
        stats['total_vehicles'])
    print 'mean total vehicle utilization (%% of day spent moving): %0.3f' % \
        (stats['total_duration'] / stats['total_vehicles'] / (24*60*time_days))

    trip_counter = Counter(stats['trips'])
    print '\nmean trips per car: %0.2f' % (np.mean(stats['trips'])),
    if abs(time_days-1.0) > 0.01:
        print ' (%0.2f per day),' % (np.mean(stats['trips']) / time_days),
    else:
        print ',',
    print 'stdev: %0.3f' % np.std(stats['trips'])
    print 'most common trip counts: %s' % trip_counter.most_common(10)
    print 'cars with zero trips: %d' % trip_counter[0]
    print 'trip count per day quartiles:'
    print format_quartiles(np.array(stats['trips'])/time_days, format='%0.2f')

    print 'mean distance per trip (km): %0.2f, stdev: %0.3f' % \
        (np.mean(stats['distances']), np.std(stats['distances']))
    print 'most common distances, rounded to nearest 0.5 km: %s' % \
        Counter(stats['distance_bins']).most_common(10)
    print trip_breakdown(stats['distances'], sorting_bins = [5, 10],
        label = lambda dist, count: 'trips over %d km: %s' % (dist, count))
    print 'distance quartiles: '
    print format_quartiles(stats['distances'])

    print 'mean duration per trip (minutes): %0.2f, stdev: %0.3f' % \
        (np.mean(stats['durations']), np.std(stats['durations']))
    print 'most common durations, rounded to nearest 5 minutes: %s' % \
        Counter(stats['duration_bins']).most_common(10)
    print trip_breakdown(stats['durations'])
    print 'duration quartiles: '
    print format_quartiles(stats['durations'], format = '%d')

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

