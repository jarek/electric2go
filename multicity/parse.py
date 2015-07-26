# coding=utf-8

from __future__ import unicode_literals


def get_cars_from_json(json_data):
    all_markers = json_data.get('marker', [])

    all_cars = [car for car in all_markers if car['hal2option']['objectname'] == 'multicitymarker']

    return all_cars


def get_license_plate(car):
    tooltip = car['hal2option']['tooltip'].replace('&nbsp;', ' ')

    start_string = '  ('
    start = tooltip.find(start_string)

    end = tooltip.find(')', start)

    plate = tooltip[start + len(start_string): end]

    return plate


def extract_car_basics(car):
    return car['hal2option']['id'], float(car['lat']), float(car['lng'])


def extract_car_data(car):
    result = {}

    vin, lat, lng = extract_car_basics(car)

    result['vin'] = vin
    result['lat'] = lat
    result['lng'] = lng

    result['license_plate'] = get_license_plate(car)
    result['name'] = result['license_plate']

    # defaults for all the cars in the system
    result['model'] = 'Citroën C-Zero'
    result['electric'] = True
    result['fuel_type'] = 'E'

    # AFAICT those are not available from the all-cars API endpoint,
    # would have to query for each car separately
    result['address'] = ''
    result['fuel'] = 0

    return result


def get_range(car):
    if 'fuel' not in car:
        car = extract_car_data(car)

    # Multicity quotes a full charge range of 150 km (NEDC).
    # Multicity policy is that cars cannot be parked with less than 10 km range
    # (presumably unless they're plugged in?).
    # https://www.multicity-carsharing.de/en/faq/how-do-i-ensure-that-the-car-battery-charge-level-does-not-fall-below-the-minimum-at-the-end-of-the-journey/
    # Use 10 km = ~7% as indicator for minimum charge level.

    if car['fuel'] > 7:
        car_range = int(1.5 * (car['fuel']-7))
    else:
        car_range = 0

    return car_range
