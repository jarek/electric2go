# coding=utf-8


def get_cars(system_data_dict):
    return system_data_dict.get('placemarks', [])


def get_cars_dict(system_data_dict):
    # This 'vin' key must match the first item returned from get_car_basics()
    return {car['vin']: car
            for car in get_cars(system_data_dict)}


def get_everything_except_cars(system_data_dict):
    result = system_data_dict.copy()
    del result['placemarks']
    return result


def get_car_basics(car):
    return car['vin'], car['coordinates'][1], car['coordinates'][0]


def get_car(car):
    result = {}

    vin, lat, lng = get_car_basics(car)

    result['vin'] = vin
    result['license_plate'] = car['name']

    result['model'] = 'smart fortwo'

    result['lat'] = lat
    result['lng'] = lng

    result['address'] = car['address']

    result['fuel'] = car['fuel']
    result['fuel_type'] = car['engineType']
    result['electric'] = (car['engineType'] == 'ED')
    result['charging'] = car.get('charging', False)

    result['transmission'] = 'A'

    result['cleanliness_interior'] = car['interior']
    result['cleanliness_exterior'] = car['exterior']

    result['app_required'] = car['smartPhoneRequired']

    return result


def get_range(car):
    if 'fuel' not in car:
        car = get_car(car)

    # Wikipedia quotes full charge range 135 km (NEDC), car2go quotes 130 km.
    # Use 130 km.
    # car2go policy is that less than 20% charge remaining requires ending
    # trip at a charging point. Use 20% as indicator for minimum charge level.

    if car['fuel'] > 20:
        car_range = int(1.3 * (car['fuel']-20))
    else:
        car_range = 0

    return car_range


def put_car(car):
    # inverse of get_car

    mapped_keys = {
        'vin': 'vin',
        'license_plate': 'name',
        'address': 'address',
        'fuel': 'fuel',
        'fuel_type': 'engineType',
        'cleanliness_interior': 'interior',
        'cleanliness_exterior': 'exterior',
        'app_required': 'smartPhoneRequired'
    }

    # everything else is assumed to be directly mapped
    directly_mapped_keys = car.keys() - mapped_keys.keys() - {
        'starting_time', 'ending_time', 'lat', 'lng',  # rewritten keys
        'transmission', 'model', 'electric'  # derived and assumed keys
    }

    formatted_car = {mapped_keys[key]: car[key] for key in mapped_keys}
    formatted_car.update({key: car[key] for key in directly_mapped_keys})

    # minor changes
    formatted_car['coordinates'] = (car['lng'], car['lat'], 0)

    if car['fuel_type'] != 'CE':
        # in the API, 'charging' key is only present on non-CE cars
        formatted_car['charging'] = car['charging']
    else:
        formatted_car.pop('charging', None)

    return formatted_car


def put_cars(cars, result_dict):
    # inverse of get_cars

    # car2go has nothing else in the API result,
    # so the result_dict param is ignored
    return {'placemarks': cars}
