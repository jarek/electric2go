# coding=utf-8


def get_cars(system_data_dict):
    return system_data_dict


def get_car_basics(car):
    return car['virtual_rental_id'], car['lat'], car['lon']


def get_car(car):
    result = {}

    vin, lat, lng = get_car_basics(car)

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
