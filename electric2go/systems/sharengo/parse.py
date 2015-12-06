# coding=utf-8


def get_cars_from_json(json_data):
    return json_data['data'] if 'data' in json_data else json_data


def extract_car_basics(car):
    return car['imei'], car['latitude'], car['longitude']


def extract_car_data(car):
    result = {}

    vin, lat, lng = extract_car_basics(car)

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
        car = extract_car_data(car)

    # Figures returned on API and website give a fairly linear 1% = 1.66 km ratio

    return car['fuel'] * 1.66
