Carshare systems
================

Systems are automatically found if a package with their name is included
in the `electric2go/systems` directory. They are imported in the
`_get_carshare_system_module()` function in `electric2go/systems/__init__.py`.
As of December 2015, a system must provide the the following:

- `[system].CITIES` dictionary
- `[system].parse` providing get_cars_from_json(), extract_car_basics(), and
  extract_car_data(). get_range() is also required if system is to be
  used on the web.

Check back from references to `_get_carshare_system_module()` if in doubt.

It will probably be easiest to add new systems by cloning contents of
an existing system and editing names, URLs, etc as needed.
Enjoy is a basic system that has multiple cities, so might be a good start.
car2go and Drivenow are currently the systems with the most features
(particularly drawing maps) so check them for more functionality.

Most code has been written with car2go in mind and might still use a few 
abstractions that aren't valid in other systems. However, any system providing
`CITIES` and `parse` as listed above should work with with the web interface,
and support analysis code and give at least somewhat meaningful statistics.
If you need to make changes to support other systems,
patches or pull requests are most welcome.
