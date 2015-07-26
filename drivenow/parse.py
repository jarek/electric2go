# coding=utf-8


def get_cars_from_json(json_data):
    if 'cars' in json_data and 'items' in json_data['cars']:
        return json_data['cars']['items']
    else:
        return []


def extract_car_basics(car):
    return car['id'], car['latitude'], car['longitude']


def extract_car_data(car):
    result = {}

    vin, lat, lng = extract_car_basics(car)

    result['vin'] = vin
    result['name'] = car['name']
    result['license_plate'] = car['licensePlate']

    result['model'] = car['modelName']
    result['color'] = car['color']

    result['lat'] = lat
    result['lng'] = lng

    result['address'] = ', '.join(car['address'])

    result['fuel'] = car['fuelLevel'] * 100
    result['fuel_type'] = car['fuelType']
    result['electric'] = (car['fuelType'] == 'E')
    result['charging'] = False

    result['transmission'] = car['transmission']

    result['cleanliness_interior'] = car['innerCleanliness']

    return result


def get_range(car):
    if 'fuel' not in car:
        # means we got a verbatim JSON object, not yet parsed to common format
        car = extract_car_data(car)

    # Wikipedia quotes 130-160 km range (NEDC), Drivenow claims up to 160 km.
    # Use 130 km exactly.
    # Drivenow policy is that less than 10 miles range remaining requires
    # ending trip at a charging point. Use 10 mi = 16 km = ~12% as indicator
    # for minimum charge level.

    if car['fuel'] > 12:
        range = int(1.3 * (car['fuel']-12))
    else:
        range = 0

    return range
