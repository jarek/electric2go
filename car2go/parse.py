#!/usr/bin/env python2
# coding=utf-8


from cars import dist

def process_data(json_data, data_time, previous_data):
    data = previous_data
    trips = []
    positions = []

    for vin in data.keys():
        # need to reset out status for cases where cars are picked up
        # (and therefore disappear from json_data) before two cycles
        # of process_data. otherwise their just_moved is never updated.
        # if necessary, just_moved will be set to true later
        data[vin]['just_moved'] = False

    for car in json_data:
        if 'vin' in car:
            vin = car['vin']
            name = car['name']
            lat = car['coordinates'][1]
            lng = car['coordinates'][0]
        else:
            # no recognized data in this file
            continue

        position_data = {'coords': [lat, lng], 'metadata': {}}

        if vin in previous_data:
            if not (data[vin]['coords'][0] == lat and data[vin]['coords'][1] == lng):
                # car has moved since last known position
                prev_coords = data[vin]['coords']
                prev_seen = data[vin]['seen']
                data[vin]['coords'] = [lat, lng]
                data[vin]['seen'] = data_time
                data[vin]['just_moved'] = True

                if 'fuel' in data[vin]:
                    prev_fuel = data[vin]['fuel']
                    data[vin]['fuel'] = car['fuel']
                    fuel_use = prev_fuel - car['fuel']

                current_trip_distance = dist(data[vin]['coords'], prev_coords)
                current_trip_duration = (data_time - prev_seen).total_seconds()

                trip_data = {
                    'vin': vin,
                    'from': prev_coords,
                    'to': data[vin]['coords'],
                    'starting_time': prev_seen,
                    'ending_time': data[vin]['seen'],
                    'distance': current_trip_distance,
                    'duration': current_trip_duration,
                    'fuel_use': 0
                    }
                if 'fuel' in data[vin]:
                    trip_data['starting_fuel'] = prev_fuel
                    trip_data['ending_fuel'] = data[vin]['fuel']
                    trip_data['fuel_use'] = fuel_use

                data[vin]['most_recent_trip'] = trip_data

                if current_trip_duration > 0:
                    data[vin]['speed'] = current_trip_distance / (current_trip_duration / 3600.0)
                    position_data['metadata']['speed'] = data[vin]['speed']

                trips.append(trip_data)

            else:
                # car has not moved from last known position. just update time last seen
                data[vin]['seen'] = data_time
                data[vin]['just_moved'] = False
        else:
            # 'new' car showing up, initialize it
            data[vin] = {'name': name, 'coords': [lat, lng], 'seen': data_time,
                'just_moved': False}
            if 'fuel' in car:
                data[vin]['fuel'] = car['fuel']

        positions.append(position_data)

    return data, positions, trips
