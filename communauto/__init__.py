#!/usr/bin/env python2
# coding=utf-8


JSONP_CALLBACK_NAME = 'electric2goscraper'


# communauto auto-mobile has only one city for now, and the service always returns it,
# so I am hardcoding the URL
API_AVAILABLE_VEHICLES_URL = lambda city: \
    'https://www.reservauto.net/WCF/LSI/LSIBookingService.asmx/GetVehicleProposals?CustomerID=&Longitude=0&Latitude=0&Callback={callback}'.format(callback=JSONP_CALLBACK_NAME)
