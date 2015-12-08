# coding=utf-8


CITIES = {
    'milano': {
        'of_interest': True
    },
    'firenze': {
        'of_interest': True
    },
    'torino': {
        'of_interest': True
    },
    'roma': {
        'of_interest': True
    }
}

# Enjoy API is a bit weird. All cities use the same API endpoint, and the city
# for which data is returned changes based on current session cookie
# set when loading a city page. Hence the API_KNOCK_URL.

API_VEHICLES_URL = 'https://enjoy.eni.com/get_vetture'
API_KNOCK_URL_FORMAT = 'https://enjoy.eni.com/it/{city}/trova_auto'

for city, city_data in CITIES.items():
    city_data['API_AVAILABLE_VEHICLES_URL'] = API_VEHICLES_URL
    city_data['API_KNOCK_HEAD_URL'] = API_KNOCK_URL_FORMAT.format(city=city)
