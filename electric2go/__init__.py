# coding=utf-8

from datetime import datetime
from math import radians, sin, cos, asin, sqrt
from subprocess import Popen, PIPE

from .files import root_dir


def current_git_revision():
    """
    Gets the current git revision in the directory of the electric2go module.
    Intended for use as metadata for information what version of the software
    generated a given output file.

    This uses `git rev-parse --verify HEAD` in the directory
    where electric2go/__init__.py is located.

    The result will usually be the current git revision of the electric2go
    codebase. There is an edge case: the result might be the revision
    of a different repository if electric2go is not a git repository,
    but a parent directory is a git repository.
    (e.g. this file is /home/user/repo/electric2go/electric2go/__init__.py,
    /home/user/repo/electric2go/electric2go/.git/ doesn't exist,
    but /home/user/repo/.git/ does)

    Raises RuntimeError when unable to find the git revision.

    This will have to be changed if electric2go is to be available as
    a package or in other cases where the files would not be expected
    to be versioned. Perhaps we can switch to MD5-summing a source .py file
    to establish quasi-revision, but that decision can be done later.
    """

    cmd = Popen(["git", "rev-parse", "--verify", "HEAD"],
                stdout=PIPE, stderr=PIPE, cwd=root_dir)

    stdout_data, stderr_data = cmd.communicate()

    if stderr_data:
        raise RuntimeError('Unable to get git revision of electric2go')

    rev = stdout_data.decode('utf-8').strip()

    return rev


def output_file_name(description, extension=''):
    file_name = '{date}_{desc}'.format(
        date=datetime.now().strftime('%Y%m%d-%H%M%S'),
        desc=description)

    if extension:
        file_name = '{name}.{ext}'.format(name=file_name, ext=extension)

    return file_name


def dist(ll1, ll2):
    # Haversine formula implementation to get distance between two points
    # adapted from http://www.movable-type.co.uk/scripts/latlong.html
    # see also http://stackoverflow.com/questions/27928/calculate-distance-between-two-ll-points
    # and http://stackoverflow.com/questions/4913349/haversine-formula-in-python

    # the js equivalent of this code is used in sort.js
    # - any changes should be reflected in both

    earth_radius = 6371  # Radius of the earth in km

    lat1, lng1 = ll1
    lat2, lng2 = ll2

    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)

    # Using d_lat = lat2_rad - lat1_rad gives marginally different results,
    # because floating point
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)

    a = sin(d_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(d_lng/2)**2
    c = 2 * asin(sqrt(a))

    return earth_radius * c
