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
