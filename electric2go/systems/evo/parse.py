# coding=utf-8


def get_cars_from_json(json_data):
    return json_data.get('data', [])


def extract_car_basics(car):
    return car['Id'], car['Lat'], car['Lon']


def extract_car_data(car):
    result = {}

    vin, lat, lng = extract_car_basics(car)

    result['vin'] = vin
    result['license_plate'] = car['Name']

    result['model'] = 'Toyota Prius C'

    result['lat'] = lat
    result['lng'] = lng

    result['address'] = car['Address']

    result['fuel'] = car['Fuel']

    return result
