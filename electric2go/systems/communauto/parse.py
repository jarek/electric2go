# coding=utf-8


def get_cars(system_data_dict):
    system_data_dict.get('Vehicules', [])


def get_car_basics(car):
    return car['Id'], car['Position']['Lat'], car['Position']['Lon']


def get_car(car):
    result = {}

    vin, lat, lng = get_car_basics(car)

    result['vin'] = vin
    result['name'] = car['Name']
    result['license_plate'] = car['Immat']

    result['model'] = car['ModelName']

    result['lat'] = lat
    result['lng'] = lng

    result['address'] = ''

    result['fuel'] = car['EnergyLevel']
    result['electric'] = (car['ModelName'] == 'LEAF')
    result['charging'] = False

    return result


def get_range(car):
    if 'fuel' not in car:
        # means we got a verbatim JSON object, not yet parsed to common format
        car = get_car(car)

    # Wikipedia quotes 120 km EPA or 200 km NEDC. Use 120 km to be safe.
    # Communauto policy requires 15 km range remaining when ending trip,
    # use 12% as indicator for minimum charge level.

    if car['fuel'] > 12:
        car_range = int(1.2 * (car['fuel']-12))
    else:
        car_range = 0

    return car_range
