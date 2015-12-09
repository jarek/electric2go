electric2go
===========

Collect and analyze data on roaming one-way carshare use.

The project started out as a way to find nearest electric car2go vehicles,
hence the name. I've since added caching the data, archiving it,
and processing to make visualizations and collect statistics.

There is now good support for other carshare systems, and as of December 2015
we can handle Drivenow, Montréal's Communauto Automobile, Vancouver's Evo,
Italy's Enjoy, Milan's Sharengo, and Berlin's floating Multicity.


Requirements
------------

Known to work under Python 3.4.2 and 2.7.8.
Scripts invoked from the command line specify `#!/usr/bin/env python3`.

PyPI dependencies for whole project are in requirements.txt,
for data archiver (run headless on a server) in requirements-download.txt,
for web interface in requirements-web.txt.


Web interface: finding electric cars
------------------------------------

Simple web page listing currently available electric carshare vehicles
in a number of cities where a system has both internal-combustion
and electric vehicles available. A basic JSON API is also available.

View it live at http://bin.piorkowski.ca/electric2go/

See [doc/web.md](doc/web.md) for more information.


Analyzing data
--------------

A carshare's data can be downloaded automatically and archived. An archive
can be then analyzed to get usage statistics and generate visualizations.

* [Example visualization video on Youtube](https://www.youtube.com/watch?v=UOqA-un8oeU)
* [Example write-ups using statistics calculated with this code](http://piorkowski.ca/rev/tag/carshare/)

See [doc/analysis.md](doc/analysis.md) for more information.


Multisystem operation
---------------------

Supported carshare systems are defined in packages in
the `electric2go/systems/` directory.

A system definition consists of a dictionary of cities a system supports
and a "parser" that converts the system's API output to a standard format. 

More systems can be added fairly easily.
See [doc/systems.md](doc/systems.md) for more information.

If you add a new system, patches or pull requests are most welcome.


Similar projects
----------------

- https://github.com/mattsacks/disposable-cars/ is a visualization of
car2go trips in Portland
- http://www.comparecarshares.com/ incorporates car2go data to calculate 
how competitive the cost is compared with driving, cycling, 
and classic carshare systems in Calgary, Vancouver, and Toronto
- http://labs.densitydesign.org/carsharing/ is an analysis of Enjoy service
in Milan, it has a making-of write-up at
http://www.densitydesign.org/2014/07/the-making-of-the-seven-days-of-carsharing-project/
- http://mappable.info/one-week-of-carsharing was an analysis of
car2go service in a number of cities, taken down by request of car2go


Legal stuff
-----------

This product uses the car2go API but is not endorsed or certified by car2go.

Released under the ISC license. Boilerplate:

Copyright (c) 2012-2015, Jarek Piórkowski <jarek@piorkowski.ca>
		
Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted, provided that the above copyright notice and this permission notice appear in all copies.
		
The software is provided "as is" and the author disclaims all warranties with regard to this software including all implied warranties of merchantability and fitness. In no event shall the author be liable for any special, direct, indirect, or consequential damages or any damages whatsoever resulting from loss of use,
data or profits, whether in an action of contract, negligence or other tortious action, arising out of or in connection with the use or performance of this software. 
