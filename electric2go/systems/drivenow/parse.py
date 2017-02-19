# coding=utf-8


KEYS = {
    'changing': {
        # must be handled manually: address

        # Note: car['rentalPrice']['isOfferDrivePriceActive'] can also change.
        # In practice I don't think it'll be a problem currently, since cars
        # are never on offer price right after being parked,
        # but it's technically not correct.

        # properties that indicate start of new parking period:
        'lat': 'latitude',
        'lng': 'longitude',

        # properties that can change during a parking period:
        'charging': 'isCharging',
        'fuel': 'fuelLevelInPercent',
        'api_estimated_range': 'estimatedRange',

        # properties that can only change during a drive:
        'cleanliness_interior': 'innerCleanliness',
        'parkingSpaceId': 'parkingSpaceId',
        'isInParkingSpace': 'isInParkingSpace'
    },

    # things that are expected to not change at all for a given car VIN/ID
    # during a reasonable timescale (1 week to 1 month)
    'unchanging': {
        # must be handled manually: electric

        'vin': 'id',

        'name': 'name',
        'license_plate': 'licensePlate',

        'model': 'modelName',
        'color': 'color',

        'fuel_type': 'fuelType',

        'transmission': 'transmission',

        # this is a dict and one of its properties can change, noted in a comment in 'changing'
        'rentalPrice': 'rentalPrice',

        # the below is extra info, not widely used, no keys are renamed
        'make': 'make',
        'group': 'group',
        'series': 'series',
        'modelIdentifier': 'modelIdentifier',
        'equipment': 'equipment',
        'carImageUrl': 'carImageUrl',
        'carImageBaseUrl': 'carImageBaseUrl',
        'routingModelName': 'routingModelName',
        'variant': 'variant',
        'isPreheatable': 'isPreheatable'
    }
}


def get_cars(system_data_dict):
    if 'cars' in system_data_dict and 'items' in system_data_dict['cars']:
        return system_data_dict['cars']['items']
    else:
        return []

    # TODO: perhaps instead duck-type system_data_dict keys and raise "wrong system" exception in case of KeyError?


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


def get_car_unchanging_properties(car):
    """
    Gets car properties that are expected to not change at all
    for a given car VIN/ID during a reasonable timescale (1 week to 1 month)
    :param car: car info in original system JSON-dict format
    :return: dict with keys mapped to common electric2go format
    """

    props = KEYS['unchanging']
    result = {key: car[props[key]] for key in props}

    # derived field that can't be done automatically with a key mapping
    result['electric'] = (car['fuelType'] == 'E')

    return result


def get_car_changing_properties(car):
    """
    Gets cars properties that change during a trip
    :param car: car info in original system JSON-dict format
    :return: dict with keys mapped to common electric2go format
    """

    result = {mapped_key: car[original_key]
              for mapped_key, original_key
              in KEYS['changing'].items()}

    # derived field that can't be done automatically with a key mapping
    result['address'] = ', '.join(car['address'])

    return result


def get_car(car):
    # TODO: this is only used by web-related things, see if they can/should be migrated

    result = get_car_unchanging_properties(car)
    result.update(get_car_changing_properties(car))

    return result


def get_range(car):
    # TODO: could try using estimatedRange if included in API response,
    # presumably Drivenow has a better estimate than we could calculate

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


def put_cars(cars, result_dict):
    # inverse of get_cars
    result = result_dict['system'].copy()
    result['cars']['items'] = cars
    result['cars']['count'] = len(cars)
    return result


def put_car(car):
    # inverse of get_car

    mapped_keys = KEYS['unchanging']
    mapped_keys.update(KEYS['changing'])

    formatted_car = {original_key: car[mapped_key]
                     for mapped_key, original_key in mapped_keys.items()}

    # minor changes
    formatted_car['address'] = car['address'].split(', ')

    # special handling, data is duplicated in source API
    # note 100.0 to trigger float division in Python 2
    formatted_car['fuelLevel'] = formatted_car['fuelLevelInPercent'] / 100.0

    return formatted_car


def get_car_parking_drift(car):
    """
    Gets properties that can change during a parking period but aren't
    considered to interrupt the parking.
    These are things like a car charging while being parked.
    :param car: must be formatted in original system JSON-dict format
    :return: a hashable object
    """

    return (car['estimatedRange'], car['fuelLevelInPercent'], car['isCharging'],
            car['rentalPrice']['isOfferDrivePriceActive'])


def put_car_parking_drift(car, d):
    """
    Update `car`'s properties that might have changed during a parking period.
    :param car: must be formatted in original system JSON-dict format
    :param d: must be a result of get_car_parking_drift()
    """

    car['estimatedRange'] = d[0]
    car['fuelLevelInPercent'] = d[1]
    # special handling, data is duplicated in source API
    # note 100.0 to trigger float division in Python 2
    car['fuelLevel'] = d[1] / 100.0
    car['isCharging'] = d[2]
    car['rentalPrice']['isOfferDrivePriceActive'] = d[3]

    return car
