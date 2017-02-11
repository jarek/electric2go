# coding=utf-8


def get_cars(system_data_dict):
    return system_data_dict.get('data', [])


def get_everything_except_cars(system_data_dict):
    result = system_data_dict.copy()
    del result['data']
    return result


def get_car_basics(car):
    return car['Id'], car['Lat'], car['Lon']


def get_car_unchanging_properties(car):
    """
    Gets car properties that are expected to not change at all
    for a given car VIN/ID during a reasonable timescale (1 week to 1 month)
    :param car: car info in original system JSON-dict format
    :return: dict with keys mapped to common electric2go format
    """

    return {
        'vin': car['Id'],
        'license_plate': car['Name'],
        'model': 'Toyota Prius C'
    }


def get_car_changing_properties(car):
    """
    Gets cars properties that change during a trip
    :param car: car info in original system JSON-dict format
    :return: dict with keys mapped to common electric2go format
    """

    return {
        'lat': car['Lat'],
        'lng': car['Lon'],
        'address': car['Address'],
        'fuel': car['Fuel']
    }


def get_car(car):
    result = {}

    vin, lat, lng = get_car_basics(car)

    result['vin'] = vin
    result['license_plate'] = car['Name']

    result['model'] = 'Toyota Prius C'

    result['lat'] = lat
    result['lng'] = lng

    result['address'] = car['Address']

    result['fuel'] = car['Fuel']

    return result


def get_car_parking_drift(car):
    """
    Gets properties that can change during a parking period but aren't
    considered to interrupt the parking.
    These are things like a car charging while being parked.
    :return: a hashable object
    """

    # TODO: implement
    return None


def put_car_parking_drift(car, d):
    """
    Update `car`'s properties that might have changed during a parking period.
    :param d: must be a result of get_car_parking_drift()
    """

    # TODO: implement
    return car
