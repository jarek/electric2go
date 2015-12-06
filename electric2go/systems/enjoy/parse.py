# coding=utf-8


def get_cars_from_json(json_data):
    return json_data


def extract_car_basics(car):
    return car['virtual_rental_id'], car['lat'], car['lon']


def extract_car_data(car):
    result = {}

    vin, lat, lng = extract_car_basics(car)

    result['vin'] = vin
    result['lat'] = lat
    result['lng'] = lng
    result['license_plate'] = car['car_plate']

    result['fuel'] = car['fuel_level']
    result['electric'] = False

    result['address'] = car['address']

    result['model'] = car['car_name']

    result['charging'] = car['charging'] if 'charging' in car else False

    return result
