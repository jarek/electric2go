Analyzing data
==============

The electric2go project has a fairly extensive library for analyzing
carshare use data.

Data is collected using `download.py` with an "archive" param.
Cities indicated as `'of_interest': True` in a system's CITIES dictionary
will have their information saved to a file named with a timestamp. 
The `doc/crontab` file has sample commands.

A data archive is then loaded into `scripts/normalize.py` to convert it
to a JSON data dictionary that is will have the same format for all
supported systems. This is printed to stdout and can either be piped
directly to another command or directed to a file for later use and reuse.

`scripts/merge.py` merges two or more JSON data dictionaries that describe
sequential time periods. For example, you can merge seven files, each with
a day's worth of data, into one file containing the whole week's data.

A number of other scripts read in JSON from stdin and process it:

`scripts/video.py` generates generating location maps of carshare vehicles at
a given time. These maps are then animated into a video that shows
car movement over time.
Sample output: https://www.youtube.com/watch?v=UOqA-un8oeU

`scripts/graph.py` generates single images, for instance a map of
all positions where cars were parked during the dataset.

Given a data dictionary, `scripts/stats.py` calculates statistics about
properties like trip distance or duration.
Keep in mind that the statistics are only as good as the data coming in.
For instance, reserved car2go cars disappear off the available vehicles list, 
so any time reserved will be counted as trip time.

The JSON data piping setup allows easy filtering of data to process.
For instance you could get statistics for a week of data for only
the morning rush hour. To do this, pipe to a filtering script between
invocations of `normalize.py` and `video.py`/`graph.py`/`stats.py`.

All of the above scripts are thin executable wrappers around modules in
`electric2go/analysis` package, which you can also import directly.

Note that all dates within the system are UTC. Provide a tz_offset param
to `video` and `stats` to compensate for timezones.

Statistics require numpy and graphing also requires matplotlib;
install the requirements with `pip install -r requirements.txt`
