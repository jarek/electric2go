electric2go
===========

Collect and analyze carshare use data, with particular focus on roaming one-way
carshares.

The project started out as a way to find nearest electric car2go vehicles,
hence the name. I've since added caching the data, archiving it, and processing
to make visualizations and collect statistics.

There is rudimentary support for other carshare systems (currently implemented
a couple of cities for DriveNow and a couple of TransLink bus routes).
download.py has been updated to support this but most other code assumes car2go.

Multisystem operation
---------------------

Systems are added by editing cars.py function get_all_cities(). It will probably
be easiest to add support by cloning contents of the existing car2go directory
(\_\_init\_\_.py, city.py, and process.py) and editing names, URLs, etc as needed.

Most code has been written with car2go in mind and might use abstractions
that aren't valid in other systems. download.py has been updated. process.py is
only hardcoded at the very beginning but might use car2go-specific concepts.
The web interface currently only supports car2go. Making everything less
car2go-specific is pretty high on the todo list.

Web interface: finding electric cars
------------------------------------

Simple web page listing currently available electric car2go vehicles in 
a car2go-serviced city. Currently hardcoded to car2go, in web_helper.py.

Preview at http://bin.piorkowski.ca/electric2go/

The page shows quick links to electric car2go listings for cities where there's
a few electric cars. (This is specified with 'electric': 'some' in CITIES
dictionary in city.py.)

This will technically work for any city listed in car2go/city.py,
though attempting to load a city with no electric cars like Toronto 
will just inform you there are 0 available, and attempting to load 
an all-electric city like San Diego or Amsterdam is an excellent way to 
kill your Google Maps free map quota with 200+ mapping requests.

As the car2go API v2.1 (current as of time of writing) does not support 
searching by engine type, the application downloads a list of all cars
available in the city and filters it before displaying.

This download is normally a couple tens of kilobytes and takes a second or two.
To speed this up, download.py can be used to download the files regularly 
and save them locally for use as a cache. The scripts will automatically 
look for a file named data/{system}/current\_$cityname and compare its last 
modified time to see if it is recent enough (default allowed age is 60 seconds).
If it is, the file will be used instead of redownloading the information. 
download.py is most useful when invoked automatically by cron or similar tool. 
A sample crontab entry is included in `crontab` file.

Files involved:

- cars.py: contains data retrieval and parsing logic
- car2go/city.py: stores list of cities with some electric cars
- index.py and web_helper.py: contains display logic and HTML pasta
- frontend/sort.js: sorts car list by distance from user's reported geolocation
- frontend/style.css

Optionally:

- download.py: caches data for faster operation
- crontab: sample crontab entry for invoking download.py

Playing with data
-----------------

process.py can be used to generate location maps of carshare vehicles at a given
time. These maps can be animated into a video that shows car movement over time.
Sample output: http://www.youtube.com/watch?v=5nveWwk3VSg

There is also functionality to collect car positions and trips over a set period
then graph them all or calculate statistics like trip distance or duration.

Some filtering of trips/positions analyzed is available and more is coming.

Currently hardcoded to car2go but most things are factored out properly so
that is about to change.

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

