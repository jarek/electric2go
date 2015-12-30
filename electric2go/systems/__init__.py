# coding=utf-8

import importlib


def _fill_in_city_information(system, city_name, city_data):
    city_data['system'] = system
    city_data['name'] = city_name

    if 'display' not in city_data:
        city_data['display'] = city_name.title()

    if 'MAP_SIZES' not in city_data and 'MAP_LIMITS' in city_data:
        # default to 1920x1080 if we have other map data
        city_data['MAP_SIZES'] = {'MAP_X': 1920, 'MAP_Y': 1080}

    # set some default values if not present
    city_data.setdefault('electric', False)
    city_data.setdefault('of_interest', False)
    city_data.setdefault('number_first_address', False)
    city_data.setdefault('API_AVAILABLE_VEHICLES_HEADERS', None)
    city_data.setdefault('API_KNOCK_HEAD_URL', None)

    # provide the range estimator
    city_data['range_estimator'] = getattr(get_parser(system), 'get_range', None)

    return city_data


def _get_carshare_system_module(system_name, module_name=''):
    if module_name == '':
        lib_name = '.{s}'.format(s=system_name)
    else:
        lib_name = '.{s}.{m}'.format(s=system_name, m=module_name)

    return importlib.import_module(lib_name, __package__)


def _get_all_cities_raw(system):
    city_module = _get_carshare_system_module(system)

    return getattr(city_module, 'CITIES')


def get_all_cities(system):
    all_cities = _get_all_cities_raw(system)

    return {city_name: _fill_in_city_information(system, city_name, all_cities[city_name])
            for city_name in all_cities}


def get_city_by_name(system, city_name):
    all_cities = _get_all_cities_raw(system)
    city_data = all_cities[city_name]
    return _fill_in_city_information(system, city_name, city_data)


def get_city_by_result_dict(result_dict):
    return get_city_by_name(result_dict['system'], result_dict['city'])


_parse_modules = {}
def get_parser(system):
    # Function with a mini-cache since getting parser requires importing
    # modules which might be pretty slow, and parsers might get requested a lot
    # Python 3 has a @functools.lru_cache but Python 2 doesn't :(
    # so hack our own simple one.
    if system not in _parse_modules:
        _parse_modules[system] = _get_carshare_system_module(system, 'parse')

    return _parse_modules[system]
