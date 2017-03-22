# coding=utf-8


KEYS = {
    'changing': {
        # must be handled manually: coordinates = (lat, lng, 0), charging
        # in the API, 'charging' key is only set on electric cars

        'address': 'address',
        'cleanliness_interior': 'interior',
        'cleanliness_exterior': 'exterior',
        'fuel': 'fuel'
    },

    # things that are expected to not change at all for a given car VIN/ID
    # during a reasonable timescale (1 week to 1 month)
    'unchanging': {
        # must be handled manually: electric

        'vin': 'vin',

        'app_required': 'smartPhoneRequired',
        'fuel_type': 'engineType',
        'license_plate': 'name'
    },

    # these are not included in the API output, previously we'd assumed
    # they were always the same, TODO: this is no longer the case
    'constant': {
        'model': 'smart fortwo',
        'transmission': 'A'
    }
}


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


def get_car_unchanging_properties(car):
    """
    Gets car properties that are expected to not change at all
    for a given car VIN/ID during a reasonable timescale (1 week to 1 month)
    :param car: car info in original system JSON-dict format
    :return: dict with keys mapped to common electric2go format
    """

    result = {mapped_key: car[original_key]
              for mapped_key, original_key
              in KEYS['unchanging'].items()}

    result.update({key: value for key, value in KEYS['constant'].items()})

    result['electric'] = (car['engineType'] == 'ED')

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

    _, lat, lng = get_car_basics(car)

    result['lat'] = lat
    result['lng'] = lng

    result['charging'] = car.get('charging', False)

    return result


def get_car(car):
    # TODO: this is only used by web-related things, see if they can/should be migrated

    vin, _, _ = get_car_basics(car)

    result = {'vin': vin}
    result.update(get_car_changing_properties(car))
    result.update(get_car_unchanging_properties(car))

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


def put_cars(cars, result_dict):
    # inverse of get_cars

    # car2go has nothing else in the API result,
    # so the result_dict param is ignored
    return {'placemarks': cars}


def put_car(car):
    # inverse of get_car

    mapped_keys = KEYS['unchanging']
    mapped_keys.update(KEYS['changing'])

    formatted_car = {original_key: car[mapped_key]
                     for mapped_key, original_key in mapped_keys.items()}

    # minor changes
    formatted_car['coordinates'] = (car['lng'], car['lat'], 0)

    # in the API, 'charging' key is only present on electric cars
    if car['electric']:
        formatted_car['charging'] = car['charging']

    return formatted_car


def get_car_parking_drift(car):
    """
    Gets properties that can change during a parking period but aren't
    considered to interrupt the parking.
    These are things like a car charging while being parked.
    :return: a hashable object
    """

    charging = car.get('charging', None)

    return car['fuel'], charging


def put_car_parking_drift(car, d):
    """
    Update `car`'s properties that might have changed during a parking period.
    :param d: must be a result of get_car_parking_drift()
    """

    car['fuel'] = d[0]

    # TODO: needs testing with a system with electric cars. I don't think there are
    # any mixed systems anymore, so just test two systems separately
    if d[1]:
        car['charging'] = d[1]

    return car
