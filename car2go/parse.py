#!/usr/bin/env python2
# coding=utf-8


from cars import dist


def get_cars_from_json(json_data):
    if 'placemarks' in json_data:
        return json_data['placemarks']
    else:
        return []


def extract_car_data(car):
    result = {}

    result['vin'] = car['vin']
    result['license_plate'] = car['name']

    result['model'] = 'smart fortwo'

    result['lat'] = car['coordinates'][1]
    result['lng'] = car['coordinates'][0]

    result['address'] = car['address']

    result['fuel'] = car['fuel']
    result['fuel_type'] = car['engineType']

    result['transmission'] = 'A'

    result['cleanliness_interior'] = car['interior']
    result['cleanliness_exterior'] = car['exterior']

    return result


def process_data(json_data, data_time, previous_data):
    data = previous_data
    trips = []
    positions = []

    # keys that are handled explicitly within the loop
    RECOGNIZED_KEYS = ['vin', 'lat', 'lng', 'fuel']

    # ignored keys that should not be tracked for trips - stuff that won't change during a trip
    IGNORED_KEYS = ['name', 'license_plate', 'address', 'model', 'color', 'fuel_type', 'transmission']

    for vin in data.keys():
        # need to reset out status for cases where cars are picked up
        # (and therefore disappear from json_data) before two cycles
        # of process_data. otherwise their just_moved is never updated.
        # if necessary, just_moved will be set to true later
        data[vin]['just_moved'] = False

    for car in get_cars_from_json(json_data):
        new_car_data = extract_car_data(car)

        OTHER_KEYS = [key for key in new_car_data.keys()
                      if key not in RECOGNIZED_KEYS and key not in IGNORED_KEYS]

        vin = new_car_data['vin']
        curr_seen = data_time
        curr_coords = [new_car_data['lat'], new_car_data['lng']]
        position_data = {'coords': curr_coords, 'metadata': {}}

        if vin in data:
            car_data = data[vin]

            if not (car_data['coords'][0] == curr_coords[0] and car_data['coords'][1] == curr_coords[1]):
                # car has moved since last known position
                prev_coords = car_data['coords']
                prev_seen = car_data['seen']
                car_data['coords'] = curr_coords
                car_data['seen'] = curr_seen
                car_data['just_moved'] = True

                prev_fuel = car_data['fuel']
                car_data['fuel'] = new_car_data['fuel']

                current_trip_distance = dist(curr_coords, prev_coords)
                current_trip_duration = (curr_seen - prev_seen).total_seconds()

                trip_data = {
                    'vin': vin,
                    'from': prev_coords,
                    'to': curr_coords,
                    'starting_time': prev_seen,
                    'ending_time': curr_seen,
                    'distance': current_trip_distance,
                    'duration': current_trip_duration,
                    'starting_fuel': prev_fuel,
                    'ending_fuel': data[vin]['fuel'],
                    'fuel_use': prev_fuel - new_car_data['fuel']
                }

                for key in OTHER_KEYS:
                    trip_data['starting_' + key] = data[vin][key]
                    trip_data['ending_' + key] = new_car_data[key]
                    data[vin][key] = new_car_data[key]

                data[vin]['most_recent_trip'] = trip_data

                data[vin]['speed'] = current_trip_distance / (current_trip_duration / 3600.0)
                position_data['metadata']['speed'] = data[vin]['speed']

                trips.append(trip_data)

            else:
                # car has not moved from last known position. just update time last seen
                car_data['seen'] = curr_seen
                car_data['just_moved'] = False

        else:
            # 'new' car showing up, initialize it
            data[vin] = {'coords': curr_coords,
                         'seen': curr_seen,
                         'fuel': new_car_data['fuel'],
                         'just_moved': False}

            for key in OTHER_KEYS:
                data[vin][key] = new_car_data[key]

        positions.append(position_data)

    return data, positions, trips
