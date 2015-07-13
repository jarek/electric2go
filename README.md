electric2go
===========

Collect and analyze carshare use data, with particular focus on roaming one-way
carshares.

The project started out as a way to find nearest electric car2go vehicles,
hence the name. I've since added caching the data, archiving it, and processing
to make visualizations and collect statistics.

There is now decent support for other carshare systems, and as of July 2015
we can handle Drivenow, Montréal's Communauto Automobile, and Vancouver's Evo.

Multisystem operation
---------------------

Systems are automatically found if a package with their name is included
in the electric2go project root directory. They are imported in the
get_carshare_system_module() function in cars.py. As of 2015-05-11,
the following modules are required for a system:

- city.py providing a CITIES dictionary
- parse.py providing get_cars_from_json(), extract_car_basics(), and
  extract_car_data(). get_range() is also required if system is to be
  used on the web.

Check references to get_carshare_system_module() if in doubt.

It will probably be easiest to add new systems by cloning contents of
the existing car2go directory (\_\_init\_\_.py, city.py, and process.py)
and editing names, URLs, etc as needed.

Most code has been written with car2go in mind and might still use abstractions
that aren't valid in other systems. However, any system providing city.py
and parse.py as listed above should work with analysis code and provide
at least somewhat meaningful statistics, and work with the web interface.
If you need to make changes to support other systems,
patches or pull requests are most welcome.

Web interface: finding electric cars
------------------------------------

Simple web page listing currently available electric carshare vehicles
in a number of cities where a system has both internal-combustion
and electric vehicles available. This is specified with 'electric': 'some'
in CITIES dictionary in {system}/city.py; supported systems are in
ALL_SYSTEMS list in web_helper.py.

Preview at http://bin.piorkowski.ca/electric2go/

Install requirements with `pip install -r requirements-web.txt`

As most carshare APIs (including car2go API v2.1, current as of time of writing)
do not support filtering cars by engine type, we download a list of all cars
available in the city and filters it before displaying.

This download is normally a couple tens of kilobytes and takes a second or two.
To speed this up, download.py can be used to download the files regularly 
and save them locally for use as a cache. The scripts will automatically 
look for a file named data/{system}/current\_{cityname} and compare its last 
modified time to see if it is recent enough (default allowed age is 60 seconds).
If it is, the file will be used instead of redownloading the information. 
download.py is most useful when invoked automatically by cron or similar tool. 
A sample crontab entry is included in `crontab` file.

Files involved:

- cars.py: contains data download and caching logic and multisystem support
- {system}/city.py: stores list of cities with some electric cars
- {system}/parse.py: in extract_car_data(), determines if a car is electric
- index.py and web_helper.py: logic and some data parsing and formatting
- api.py: provide the same information in JSON form
- frontend/*html: Jinja2 templates with HTML markup
- frontend/sort.js: sorts car list by distance from user's reported geolocation
- frontend/style.css

Optionally:

- download.py: caches data for faster operation
- crontab: sample crontab entry for invoking download.py
- google_api_key: create this file, containing only the key string,
in the same directory as index.py if you want to send an API key
with the Google Maps Static API request, see
https://developers.google.com/maps/documentation/staticmaps/#api_key for more.

Playing with data
-----------------

process.py can be used to generate location maps of carshare vehicles at a given
time. These maps can be animated into a video that shows car movement over time.
Sample output: http://www.youtube.com/watch?v=5nveWwk3VSg

There is also functionality to collect car positions and trips over a set period
then graph them all or calculate statistics like trip distance or duration.

Some filtering of trips/positions analyzed is available and more is coming.

process.py -h describes the arguments it supports.

Data is collected with download.py. Cities indicated as 'of\_interest': 'some' 
in CITIES dictionary in city.py will have their information saved to 
an appropriately-named file every cars.DATA\_COLLECTION\_INTERVAL\_MINUTES.

There is also some basic statistics (-s) and vehicle tracing (-t).
Keep in mind that the statistics are only as good as the data coming in.
For instance, reserved cars disappear off the available vehicles list, 
so any time reserved will be counted as trip time.

Files involved:

- cars.py: data retrieval logic and constants
- download.py: downloads and saves information for selected cities
- crontab: sample crontab entry for invoking download.py
- {system}/city.py: stores list of known cities and their properties
- {system}/parse.py: gets trips from collected files
- process.py: creates maps and visualizations based on the data
- backgrounds/\* - city maps from openstreetmap used as video backgrounds

Similar projects
----------------

- https://github.com/mattsacks/disposable-cars/
- http://www.comparecarshares.com/

Legal stuff
-----------

This product uses the car2go API but is not endorsed or certified by car2go.

Released under the ISC license. Boilerplate:

Copyright (c) 2012-2015, Jarek Piórkowski <jarek@piorkowski.ca>
		
Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted, provided that the above copyright notice and this permission notice appear in all copies.
		
The software is provided "as is" and the author disclaims all warranties with regard to this software including all implied warranties of merchantability and fitness. In no event shall the author be liable for any special, direct, indirect, or consequential damages or any damages whatsoever resulting from loss of use,
data or profits, whether in an action of contract, negligence or other tortious action, arising out of or in connection with the use or performance of this software. 

