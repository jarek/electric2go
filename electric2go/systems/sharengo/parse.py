# coding=utf-8


def get_cars(system_data_dict):
    return system_data_dict['data'] if 'data' in system_data_dict else system_data_dict


def get_car_basics(car):
    return car['imei'], car['latitude'], car['longitude']


def get_car(car):
    result = {}

    vin, lat, lng = get_car_basics(car)

    result['vin'] = vin
    result['lat'] = lat
    result['lng'] = lng
    result['license_plate'] = car['plate']

    result['fuel'] = car['battery']
    result['electric'] = True

    result['address'] = ''

    result['model'] = car['model']

    result['cleanliness_interior'] = car['intCleanliness']
    result['cleanliness_exterior'] = car['extCleanliness']

    result['charging'] = car['charging'] if 'charging' in car else False

    return result


def get_range(car):
    if 'fuel' not in car:
        car = get_car(car)

    # Figures returned on API and website give a fairly linear 1% = 1.66 km ratio

    return car['fuel'] * 1.66
