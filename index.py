#!/usr/bin/env python
# coding=utf-8

import time
import cars

timer = []

def format_car(car):
	for key in car:
		if isinstance(car[key], basestring):
			car[key] = car[key].encode('ascii','xmlcharrefreplace')

	coords = str(car['coordinates'][1]) + ',' + str(car['coordinates'][0])

	info = '<p data-loc="' + coords + '">'
	info += 'Location: ' + car['address'] + '<br/>'

	charge = car['fuel']
	if charge < 20:
		info += '<span style="color: red">Not driveable</span>, '
	else:
		# full charge range is approx 135 km, round down a bit
		# must end trip with more than 20% unless at charging station
		range = 1.2 * (charge-20)
		info += 'Approx range: ' + str(range) + ' km, '

	info += 'charge: ' + str(charge) + '%'

	if car['charging']:
		info += ', charging<br/>'
	else:
		info += '<br/>'

	info += 'Plate: ' + car['name'] + '<br/>'
	info += 'Interior: ' + car['interior'] + \
		', exterior: ' + car['exterior'] + '<br/>\n'

	mapurl = cars.MAPS_URL.replace('{ll}', coords).replace('{q}', car['address'].replace(' ','%20'))
	info += 'Coords: <a href="' + mapurl + '">' + coords + '</a>'
	info += '<span class="distance" data-template=", approx distance: {dist} km"></span><br/>\n'

	info += '<a href="' + mapurl + '">'
	info += cars.MAPS_IMAGE_CODE.replace('{ll}', coords).replace('{q}', car['address'])
	info += '</a>'

	return info

def get_formatted_electric_cars(city):
	electric_cars,cache = cars.get_electric_cars(city)
	result = []

	for car in electric_cars:
		result.append(format_car(car))

	return result,cache

def get_formatted_all_cities(requested_city):
	formatted_cities = []

	for city,data in sorted(cars.CITIES.iteritems()):
		# show only cities that have some electric cars,
		# but not a full fleet of electric.
		# there's nothing to show for cities that don't have any,
		# and there's no benefit over official apps for all-fleet.
		if data['electric'] == 'some':
			if city == requested_city:
				formatted_cities.append('<strong>' + data['display'] + '</strong>')
			else:
				formatted_cities.append('<a href="?city=' + city + '">' + data['display'] + '</a>')

	return '<p>car2go cities with a few electric vehicles: ' + ', '.join(formatted_cities)

def print_timer_info(t = timer):
	for timepoint in t:
		print '<!--%s: %f-->' % (timepoint[0], timepoint[1])

def print_all_html():
	print 'Content-type: text/html\n'

	ttime1 = time.time()

	requested_city = cars.get_city()

	print '<!doctype html>'
	print '<meta charset="utf-8" />'
	print '<title>electric car2go vehicles in ' + cars.CITIES[requested_city]['display'] + '</title>'

	print get_formatted_all_cities(requested_city)

	electric_cars,cache = get_formatted_electric_cars(requested_city)

	count = len(electric_cars)
	plural = 's' if count != 1 else ''

	print '<p>' + str(count) + ' electric car' + plural,
	print 'currently available in ' + cars.CITIES[requested_city]['display']

	print '<section class="sortable">'
	for car in electric_cars:
		print car
	print '</section>'

	ttime2 = time.time()
	timer.append(['total, ms', (ttime2-ttime1)*1000.0])

	print '<p><small>',
	if cache:
		print 'Using cached data. Data age: %i seconds, next refresh in %i seconds.' % (cache, cars.CACHE_PERIOD - cache)
	print 'This product uses the car2go API but is not endorsed or certified by car2go.</small></p>'

	print """
<script type="text/javascript">
function get_location() {
	try {
		// enableHighAccuracy is left to default to false
		// timeout is 2 seconds, to reposition cars reasonably quickly
		// maximum age is a minute, users are unlikely to move fast
		navigator.geolocation.getCurrentPosition(order_cars, 
			handle_error, {timeout: 2000, maximumAge: 60000});
	} catch(err) {
		// fail silently
	}
}

function handle_error(err) {
	// do nothing. fallback is default ordering, which is acceptable
}

function order_cars(position) {
	try {
		var user_lat = position.coords.latitude;
		var user_lng = position.coords.longitude;

		// get a list of all car latlngs and calculate
		// distances from user's position
		var car_list = document.querySelectorAll(".sortable p");
		var cars = [];
		for (var i = 0; i < car_list.length; i++) {
			car_latlng = car_list[i].getAttribute("data-loc")
				.split(",");
			cars.push([calculate_distance(user_lat, user_lng,
				car_latlng[0], car_latlng[1]), car_list[i]]);
		}

		// sort based on distance
		cars.sort(function(a, b) {
			a = a[0];
			b = b[0];
			return a < b ? -1 : (a > b ? 1 : 0);
		})

		// sort list of cars based on distance,
		// and add in the approx distance
		var section = document.querySelectorAll(".sortable")[0];
		for (var i = 0; i < cars.length; i++) {
			var dist = cars[i][0];
			var para = cars[i][1];
			
			// removes it wherever it was and appends in new order
			section.removeChild(para);
			section.appendChild(para);

			var dist_span = para.querySelectorAll(".distance")[0];
			var dist_str = dist_span.getAttribute("data-template");
			// also trim distance to one decimal digit
			dist_str = dist_str.replace("{dist}", dist.toFixed(1));
			dist_span.innerHTML = dist_str;
		}
	} catch (err) {
		// fail silently
	}
}

function calculate_distance(lat1, lng1, lat2, lng2) {
	// from http://www.movable-type.co.uk/scripts/latlong.html
	// see also http://stackoverflow.com/questions/27928
	function deg2rad(deg) {
		return deg * (Math.PI/180);
	}

	var R = 6371; // Radius of the earth in km
	var dLat = deg2rad(lat2-lat1);
	var dLon = deg2rad(lng2-lng1); 
	var a = 
		Math.sin(dLat/2) * Math.sin(dLat/2) +
		Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) * 
		Math.sin(dLon/2) * Math.sin(dLon/2); 
	var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)); 
	var d = R * c; // Distance in km
	return d;
}

document.onload = get_location();
</script>"""

	print_timer_info(cars.timer)
	print_timer_info()


if __name__ == '__main__':
	print_all_html()
