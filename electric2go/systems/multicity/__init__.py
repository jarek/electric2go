# coding=utf-8


# from https://www.multicity-carsharing.de/en/
# needs additional requests per car to get fuel/charge and address,
# could see if I can find a better API endpoint.

CITIES = {
    'berlin': {
        'of_interest': True,
        'electric': 'all',
        'API_AVAILABLE_VEHICLES_URL': 'https://kunden.multicity-carsharing.de/kundenbuchung/hal2ajax_process.php?searchmode=buchanfrage&lat=52.51&lng=13.39&instant_access=J&ajxmod=hal2map&callee=getMarker&objectname=multicitymarker'
    }
}


def get_latlng_extent():
    import requests
    from lxml import etree
    from ..drivenow import city as drivenow_city

    # this URL is in https://www.multicity-carsharing.de/wp-content/plugins/multicity_map/multicity.js
    # which as of 2016-05-29 is loaded by https://www.multicity-carsharing.de/
    r = requests.get('https://www.multicity-carsharing.de/wp-content/plugins/multicity_map/geschaeftsbereich_07032014.kml')

    xml = etree.fromstring(r.content)

    ns = '{http://earth.google.com/kml/2.2}'
    pl = xml.findall('.//' + ns + 'Placemark')

    # reuse code from Drivenow to parse the KML
    coords = drivenow_city.get_details_from_kml(pl[0], ns)
    return drivenow_city.get_max_latlng(coords)
