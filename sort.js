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
		var car_list = document.querySelectorAll(".sort");
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
		for (var i = 0; i < cars.length; i++) {
			var dist = cars[i][0];
			var para = cars[i][1];

			if (cars.length > 1) {
				// sort the list
				var parent = para.parentNode;

				if (i == 0)
					// cars[1] is guaranteed to exist now
					var prev = cars[1][1];
				else
					var prev = cars[i-1][1];

				// removes it wherever it was and appends 
				// in new order. first one gets appended 
				// wherever as long as it's within the list
				// (here, after the next one), and the rest are
				// appended after it in order

				// doing it this way allows having the list 
				// in DOM root, next to header/footer, without
				// requiring a wrapping element
				parent.removeChild(para);
				parent.insertBefore(para, prev.nextSibling);
			}

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

