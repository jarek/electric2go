# coding=utf-8


# from https://www.multicity-carsharing.de/en/
# needs additional requests per car to get fuel/charge and address,
# could see if I can find a better API endpoint.

CITIES = {
    'berlin': {
        'of_interest': True,
        'electric': 'all',
        'API_AVAILABLE_VEHICLES_URL': 'https://kunden.multicity-carsharing.de/kundenbuchung/hal2ajax_process.php?searchmode=buchanfrage&lat=52.51&lng=13.39&instant_access=J&ajxmod=hal2map&callee=getMarker&objectname=multicitymarker',
        'BOUNDS': {
            # actual bounds based on operation area are
            # 52.55798, 52.449909, 13.48569, 13.26054

            # use slightly wider values to allow for GPS wobble
            'NORTH': 52.559,
            'SOUTH': 52.449,
            'EAST': 13.486,
            'WEST': 13.260
        },
        'DEGREE_LENGTHS': {
            # for latitude 52.52
            'LENGTH_OF_LATITUDE': 111277.17,
            'LENGTH_OF_LONGITUDE': 67879.39
        },
        'MAP_LIMITS': {
            # Use wider limits so that the generated image will look the same
            # as car2go and Drivenow images.
            # At 1920x1080 pixels, 16:9, the map is:
            # http://render.openstreetmap.org/cgi-bin/export?bbox=13.099773,52.38927,13.646893,52.576767&scale=113281&format=png
            'NORTH': 52.576767,
            'SOUTH': 52.38927,
            'EAST': 13.646893,
            'WEST': 13.099773
        }
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
