# coding=utf-8


def get_cars(system_data_dict):
    return system_data_dict


def get_car_basics(car):
    return car['VehicleNo'], car['Latitude'], car['Longitude']


def get_car(car):
    result = {}

    vin, lat, lng = get_car_basics(car)

    result['vin'] = vin

    result['lat'] = lat
    result['lng'] = lng

    result['timestamp'] = car['RecordedTime']  # TODO: needs to be parsed, is in format like "03:58:21 pm"

    result['fuel'] = 0  # not reported in Translink API

    return result
