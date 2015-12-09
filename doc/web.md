Web interface
=============

The scripts in `web/` directory of the repository implement a simple web page
listing currently available electric carshare vehicles
in a number of cities where a system has both internal-combustion
and electric vehicles available. This is specified with `'electric': True`
in a system's `CITIES` dictionary; supported systems are listed in
`ALL_SYSTEMS` in `web/web_helper.py`. The code for displaying an HTML page
is in `web/index.py` and there is also a `web/api.py` script outputting JSON.

Preview at http://bin.piorkowski.ca/electric2go/

The webpage requires Jinja2 and requests; install requirements with
`pip install -r requirements-web.txt`

The webpage uses Google Maps Static API; to get more generous usage limits,
register for an API key and put it in a file called `google_api_key`
in the same directory as index.py. See
https://developers.google.com/maps/documentation/staticmaps/#api_key for more.

As most carshare APIs do not support filtering cars by engine type, we
download a list of all cars available in the city and filter it ourselves.

This download is normally a few dozen kilobytes and takes a second or two.
To speed this up, `download.py` can be used to download the files regularly 
and save them locally for use as a cache. The scripts will automatically 
look for a file named `data/{system}/current_{cityname}` and compare its
last modified time to see if it is recent enough (default allowed age is
60 seconds). `download.py` is most useful when invoked automatically by cron
or a similar tool. A sample crontab entry is included in `doc/crontab` file.
