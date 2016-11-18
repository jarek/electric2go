# coding=utf-8


CITIES = {
    # NOTE: Sharengo has one API endpoint, but as of 2016-11-18 it returns
    # cars in three different cities/operating areas (Milan, Florence, Rome).
    # Check car['fleet']['name'] or car['fleet']['code'] to distinguish them.
    'milano': {
        'of_interest': True,
        'electric': 'all',
        'API_AVAILABLE_VEHICLES_URL': 'https://www.sharengo.it/core/publiccars'
    }
}
