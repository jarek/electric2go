# coding=utf-8


def get_cars(system_data_dict):
    if 'cars' in system_data_dict and 'items' in system_data_dict['cars']:
        return system_data_dict['cars']['items']
    else:
        return []


def get_cars_dict(system_data_dict):
    # This 'id' key must match the first item returned from get_car_basics()
    return {car['id']: car
            for car in get_cars(system_data_dict)}


def get_everything_except_cars(system_data_dict):
    result = system_data_dict.copy()
    del result['cars']['items']
    return result


def get_car_basics(car):
    return car['id'], car['latitude'], car['longitude']


def get_car(car):
    result = {}

    vin, lat, lng = get_car_basics(car)

    result['vin'] = vin
    result['name'] = car['name']
    result['license_plate'] = car['licensePlate']

    result['model'] = car['modelName']
    result['color'] = car['color']

    result['lat'] = lat
    result['lng'] = lng

    result['address'] = ', '.join(car['address'])

    result['fuel'] = car['fuelLevelInPercent']
    result['fuel_type'] = car['fuelType']
    result['electric'] = (car['fuelType'] == 'E')
    result['charging'] = car['isCharging']

    result['transmission'] = car['transmission']

    result['cleanliness_interior'] = car['innerCleanliness']

    result['api_estimated_range'] = car['estimatedRange']  # TODO: drivenow api returns this for petrol cars as well, not sure how to handle
    result['parkingSpaceId'] = car['parkingSpaceId']
    result['isInParkingSpace'] = car['isInParkingSpace']

    unchanging_keys = {'make', 'group', 'series', 'modelIdentifier', 'equipment',
                       'carImageUrl', 'carImageBaseUrl', 'routingModelName', 'variant', 'rentalPrice', 'isPreheatable'}
    for key in unchanging_keys:
        result[key] = car[key]

    return result


def get_range(car):
    if 'fuel' not in car:
        # means we got a verbatim JSON object, not yet parsed to common format
        car = get_car(car)

    # Wikipedia quotes 130-160 km range (NEDC), Drivenow claims up to 160 km.
    # Use 130 km exactly.
    # Drivenow policy is that less than 10 miles range remaining requires
    # ending trip at a charging point. Use 10 mi = 16 km = ~12% as indicator
    # for minimum charge level.

    if car['fuel'] > 12:
        car_range = int(1.3 * (car['fuel']-12))
    else:
        car_range = 0

    return car_range


def put_car(car):
    # inverse of get_car

    mapped_keys = {
        'vin': 'id',
        'lat': 'latitude',
        'lng': 'longitude',
        'name': 'name',
        'license_plate': 'licensePlate',
        'address': 'address',

        'model': 'modelName',
        'color': 'color',

        'fuel': 'fuelLevelInPercent',
        'fuel_type': 'fuelType',
        'charging': 'isCharging',

        'transmission': 'transmission',

        'cleanliness_interior': 'innerCleanliness',

        'api_estimated_range': 'estimatedRange',
        'parkingSpaceId': 'parkingSpaceId',
        'isInParkingSpace': 'isInParkingSpace'
    }
    directly_mapped_keys = car.keys() - mapped_keys.keys() - {
        'electric',  # because 'electric' is a derived field
        'starting_time', 'ending_time'  # computed fields
    }

    formatted_car = {mapped_keys[key]: car[key] for key in mapped_keys}
    formatted_car.update({key: car[key] for key in directly_mapped_keys})

    # minor changes
    formatted_car['fuelLevel'] = formatted_car['fuelLevelInPercent'] / 100
    formatted_car['address'] = formatted_car['address'].split(', ')

    return formatted_car


def put_cars(cars, result_dict):
    # inverse of get_cars
    result = result_dict['system'].copy()
    result['cars']['items'] = cars
    return result
