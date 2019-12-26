# coding=utf-8

from __future__ import unicode_literals


JSONP_CALLBACK_NAME = 'electric2goscraper'

# communauto auto-mobile has only one city for now, and the service always returns it,
# so I am hardcoding the URL
API_URL = 'https://www.reservauto.net/WCF/LSI/Cache/LSIBookingService.svc/GetVehicleProposals'

CITIES = {
    'montreal': {
        'display': 'Montréal',
        'electric': 'some',
        'of_interest': True,
        'API_AVAILABLE_VEHICLES_URL': API_URL.format(callback=JSONP_CALLBACK_NAME),
        'JSONP_CALLBACK_NAME': JSONP_CALLBACK_NAME
    }
}
