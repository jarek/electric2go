# coding=utf-8


def get_cars(system_data_dict):
    if 'placemarks' in system_data_dict:
        return system_data_dict['placemarks']
    else:
        return []


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
    result['charging'] = car['charging'] if 'charging' in car else False

    result['transmission'] = 'A'

    result['cleanliness_interior'] = car['interior']
    result['cleanliness_exterior'] = car['exterior']

    return result


def get_range(car):
    if 'fuel' not in car:
        car = get_car(car)

    # Wikipedia quotes full charge range 135 km (NEDC), car2go quotes 130 km.
    # Use 130 km.
    # car2go policy is that less than 20% charge remaining requires ending
    # trip at a charging point. Use 20% as indicator for minimum charge level.

    if car['fuel'] > 20:
        range = int(1.3 * (car['fuel']-20))
    else:
        range = 0

    return range