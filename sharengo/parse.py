# coding=utf-8


def get_cars_from_json(json_data):
    return json_data


def extract_car_basics(car):
    return car['plate'], car['latitude'], car['longitude']


def extract_car_data(car):
    result = {}

    vin, lat, lng = extract_car_basics(car)

    result['vin'] = vin
    result['lat'] = lat
    result['lng'] = lng
    result['license_plate'] = vin

    result['fuel'] = car['battery']

    result['model'] = car['model']

    result['cleanliness_interior'] = car['int_cleanliness']
    result['cleanliness_exterior'] = car['ext_cleanliness']

    return result
