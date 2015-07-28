#!/usr/bin/env python2
# coding=utf-8

from datetime import timedelta
from collections import OrderedDict
import time
import matplotlib.pyplot as plt
import numpy as np

from cars import get_all_cities
from city_helper import is_latlng_in_bounds, get_mean_pixel_size


# speed ranges are designated as: 0-5; 5-15; 15-30; 30+
SPEED_CUTOFFS = [5, 15, 30, float('inf')]
SPEED_COLOURS = ['r', 'y', 'g', 'b']


timer = []


# strictly not correct as lat/lng isn't a grid, but close enough at city scales
def map_latitude(city_data, latitudes):
    south = city_data['MAP_LIMITS']['SOUTH']
    north = city_data['MAP_LIMITS']['NORTH']
    return ((latitudes - south) / (north - south)) * city_data['MAP_SIZES']['MAP_Y']


def map_longitude(city_data, longitudes):
    west = city_data['MAP_LIMITS']['WEST']
    east = city_data['MAP_LIMITS']['EAST']
    return ((longitudes - west) / (east - west)) * city_data['MAP_SIZES']['MAP_X']


def make_graph_axes(city_data, background=None, log_name=''):
    """
    Sets up figure area and axes for a city to be graphed.
    :param background: path to an image file to load,
    or a matplotlib.imshow()-compatible value, or None
    :param log_name: used for logging only
    :return: tuple(matplotlib_fig, matplotlib_ax)
    """

    # set up figure area

    global timer

    time_plotsetup_start = time.time()

    dpi = 80
    # i actually have no idea why this is necessary, but the 
    # figure sizes are wrong otherwise. ???
    dpi_adj_x = 0.775
    dpi_adj_y = 0.8

    # TODO: verify the timings for the comments below, if the 20-50 ms is
    # now insignificant (e.g. save is 500 ms every time...)
    # TODO: the two below take ~20 ms. try to reuse
    f = plt.figure(dpi=dpi)
    f.set_size_inches(city_data['MAP_SIZES']['MAP_X']/dpi_adj_x/dpi,
                      city_data['MAP_SIZES']['MAP_Y']/dpi_adj_y/dpi)

    # TODO: this takes 50 ms each time. try to reuse the whole set of axes
    # rather than regenerating it each time
    ax = f.add_subplot(111)
    ax.axis([0, city_data['MAP_SIZES']['MAP_X'], 0, city_data['MAP_SIZES']['MAP_Y']])

    # remove visible axes and figure frame
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)
    ax.set_frame_on(False)

    try:
        # support passing in path to an image file.
        # matplotlib's processing makes the image look a bit worse than
        # the original map - so keeping the generated graph transparent 
        # and overlaying it on source map post-render is a good option too
        background = plt.imread(background)
    except TypeError:
        # not an image path, ignore
        pass

    if background is not None:
        ax.imshow(background, origin='lower', aspect='auto')

    timer.append((log_name + ': make_graph_axes, ms',
                  (time.time()-time_plotsetup_start)*1000.0))

    return f, ax


def plot_points(ax, points, colour, symbol):
    ys, xs = zip(*points)

    ax.plot(xs, ys, colour + symbol)

    return ax


def plot_geopoints(ax, city_data, geopoints_dict, symbol):
    for colour in geopoints_dict:
        if len(geopoints_dict[colour]):
            lats, lngs = zip(*geopoints_dict[colour])

            latitudes = map_latitude(city_data, np.array(lats))
            longitudes = map_longitude(city_data, np.array(lngs))

            ax = plot_points(ax, zip(latitudes, longitudes), colour, symbol)

    return ax


def plot_lines(ax, lines_start_y, lines_start_x, lines_end_y, lines_end_x, colour='#aaaaaa'):
    for i in range(len(lines_start_y)):
        l = plt.Line2D([lines_start_x[i], lines_end_x[i]],
                       [lines_start_y[i], lines_end_y[i]],
                       color=colour)
        ax.add_line(l)

    return ax


def plot_geolines(ax, city_data, lines_start_lat, lines_start_lng, lines_end_lat, lines_end_lng, colour='#aaaaaa'):
    # translate into map coordinates
    lines_start_y = map_latitude(city_data, np.array(lines_start_lat))
    lines_start_x = map_longitude(city_data, np.array(lines_start_lng))
    lines_end_y = map_latitude(city_data, np.array(lines_end_lat))
    lines_end_x = map_longitude(city_data, np.array(lines_end_lng))

    return plot_lines(ax, lines_start_y, lines_start_x, lines_end_y, lines_end_x, colour)


def plot_trips(ax, city_data, trips, colour='#aaaaaa'):
    lines_start_lat = [t['from'][0] for t in trips]
    lines_start_lng = [t['from'][1] for t in trips]
    lines_end_lat = [t['to'][0] for t in trips]
    lines_end_lng = [t['to'][1] for t in trips]

    return plot_geolines(ax, city_data, lines_start_lat, lines_start_lng, lines_end_lat, lines_end_lng, colour)


def filter_positions_to_bounds(city_data, positions):
    """
    Filters the list of positions to only include those that in graphing bounds for the given city
    """

    return [p for p in positions if is_latlng_in_bounds(city_data, p['coords'])]


def create_points_default_colour(positions):
    """
    Assigns a default colour to all positions in the list
    :returns a dict of lists formatted suitably for passing to plot_geopoints()
    """

    return {
        SPEED_COLOURS[-1]: [p['coords'] for p in positions]
    }


def create_points_speed_colour(positions):
    """
    Extracts a list of all positions ordered by colour according to vehicle speed
    from a list of objects with metadata.
    :returns a dict of lists formatted suitably for passing to plot_geopoints()
    """

    collected = dict((colour, []) for colour in SPEED_COLOURS)

    for position in positions:
        # default to the last colour
        classification = SPEED_COLOURS[-1]

        if 'speed' in position['metadata']:
            # find the right speed basket
            for i in range(len(SPEED_CUTOFFS)):
                if position['metadata']['speed'] < SPEED_CUTOFFS[i]:
                    classification = SPEED_COLOURS[i]
                    break

        collected[classification].append(position['coords'])

    return collected


def create_points_trip_start_end(trips, from_colour='b', to_colour='r'):
    """
    Extracts a list of all start and end positions for provided trips.
    :returns a dict of lists formatted suitably for passing to plot_geopoints()
    """

    # Using OrderedDict to always return the end of the trip last
    # to ensure "to" points appear on top in the graph.
    # In plot_geopoints, points are plotted in the order of the
    # colour-key dictionary, and depending on the colours being used,
    # either "from" or "to" points could end up on top.
    # (E.g. on my implementation, "g" points would be drawn after "b",
    # which would be drawn after "r" -
    # this would vary depending on hash function in use.)
    # With OrderedDict, I specify the order.
    return OrderedDict([
        (from_colour, [trip['from'] for trip in trips]),
        (to_colour, [trip['to'] for trip in trips])
    ])


def graph_wrapper(city_data, plot_function, image_name, background=None):
    """
    Handles creating the figure, saving it as image, and closing the figure.
    :param plot_function: function accepting f, ax params to actually draw on the figure
    :param image_name: image will be saved with this name
    :param background: background for the figure (accessibility snapshot, etc)
    :return: none
    """

    global timer

    log_name = image_name
    if log_name.endswith('.png'):
        log_name = log_name[:-4]

    # set up axes
    f, ax = make_graph_axes(city_data, background, log_name)

    # pass axes back to function to actually do the plotting
    plot_function(f, ax)

    time_save_start = time.time()

    # render graph to file
    # saving as .png takes about 130-150 ms
    # saving as .ps or .eps takes about 30-50 ms
    # .svg is about 100 ms - and preserves transparency
    # .pdf is about 80 ms
    # svg and e/ps would have to be rendered before being animated, though
    # possibly making it a moot point
    f.savefig(image_name, bbox_inches='tight', pad_inches=0, dpi=80, transparent=True)

    # close the plot to free the memory. memory is never freed otherwise until
    # script is killed or exits.
    # this line causes a matplotlib backend RuntimeError in a close_event()
    # function ("wrapped C/C++ object of %S has been deleted") in every second
    # iteration, but this appears to be async from main thread and
    # doesn't appear to influence the correctness of output,
    # so I'll leave it as is for the time being
    plt.close(f)

    timer.append((log_name + ': graph_wrapper save figure, ms',
                  (time.time()-time_save_start)*1000.0))


def make_graph(system, city, positions, trips, image_filename, turn,
               show_speeds, highlight_distance, symbol, tz_offset):
    """ Creates and saves matplotlib figure for provided positions and trips. """

    global timer

    city_data = get_all_cities(system)[city]

    log_name = str(turn)

    # filter to only vehicles that are in city's graphing bounds
    filtered_positions = filter_positions_to_bounds(city_data, positions)

    if highlight_distance:
        positions_without_metadata = [p['coords'] for p in filtered_positions]
        graph_background = make_accessibility_background(city_data, positions_without_metadata, highlight_distance, log_name)
    else:
        graph_background = None

    # mark with either speed, or default colour
    if show_speeds:
        positions_by_colour = create_points_speed_colour(filtered_positions)
    else:
        positions_by_colour = create_points_default_colour(filtered_positions)

    # define what to add to the graph
    def plotter(f, ax):
        time_plot_start = time.time()

        # plot points for vehicles
        ax = plot_geopoints(ax, city_data, positions_by_colour, symbol)

        # add in lines for moving vehicles
        if len(trips) > 0:
            ax = plot_trips(ax, city_data, trips)

        # add labels
        printed_time = turn + timedelta(0, tz_offset*3600)

        coords = city_data['LABELS']['lines']
        fontsizes = city_data['LABELS']['fontsizes']

        ax.text(coords[0][0], coords[0][1],
                city_data['display'], fontsize=fontsizes[0])
        # prints something like "December 10, 2014"
        ax.text(coords[1][0], coords[1][1],
                '{d:%B} {d.day}, {d.year}'.format(d=printed_time),
                fontsize=fontsizes[1])
        # prints something like "Wednesday, 04:02"
        ax.text(coords[2][0], coords[2][1],
                '{d:%A}, {d:%H}:{d:%M}'.format(d=printed_time),
                fontsize=fontsizes[2])
        ax.text(coords[3][0], coords[3][1],
                'available cars: %d' % len(filtered_positions),
                fontsize=fontsizes[3])

        timer.append((log_name + ': make_graph plot and label, ms',
                      (time.time()-time_plot_start)*1000.0))

    # create and save plot
    graph_wrapper(city_data, plotter, image_filename, graph_background)


def make_positions_graph(system, city, data_dict, image_name, symbol):
    global timer

    time_positions_graph_start = time.time()

    city_data = get_all_cities(system)[city]

    # positions are "unfinished parkings" (cars still parked at the end of the dataset)
    # plus all of the "finished parkings" (cars that were parked at one point but moved)
    positions = [p for p in data_dict['unfinished_parkings'].values()]
    for vin in data_dict['finished_parkings']:
        positions.extend(data_dict['finished_parkings'][vin])

    filtered = filter_positions_to_bounds(city_data, positions)
    coloured = create_points_default_colour(filtered)

    def plotter(f, ax):
        plot_geopoints(ax, city_data, coloured, symbol)

    graph_wrapper(city_data, plotter, image_name, background=None)

    timer.append((image_name + ': make_positions_graph total, ms',
                  (time.time()-time_positions_graph_start)*1000.0))


def make_trips_graph(system, city, trips, image_name):
    global timer

    time_trips_graph_start = time.time()

    city_data = get_all_cities(system)[city]

    def plotter(f, ax):
        if len(trips) > 0:
            plot_trips(ax, city_data, trips)

    graph_wrapper(city_data, plotter, image_name, background=None)

    timer.append((image_name + ': make_trips_graph total, ms',
                  (time.time()-time_trips_graph_start)*1000.0))


def make_trip_origin_destination_graph(system, city, trips, image_name, symbol):
    global timer

    time_trips_graph_start = time.time()

    city_data = get_all_cities(system)[city]

    # TODO: use hexbin instead of just drawing points, to avoid problem/unexpected results
    # caused when a trip ends in a given point then the vehicle is picked up again
    # and a second trip starts in the same point (described in a comment in
    # create_points_trip_start_end()).
    # Maybe try to assign value of +1 to trips starting at a point,
    # -1 to trips ending, then do hexbin on sum or mean of the values
    # to find spots where vehicles mostly arrive, mostly depart, or are balanced

    def plotter(f, ax):
        trip_points = create_points_trip_start_end(trips)
        plot_geopoints(ax, city_data, trip_points, symbol)

    graph_wrapper(city_data, plotter, image_name, background=None)

    timer.append((image_name + ': make_trip_origin_destination_graph total, ms',
                  (time.time()-time_trips_graph_start)*1000.0))


def make_accessibility_background(city_data, positions, distance, log_name):
    global timer

    latitudes, longitudes = zip(*positions)
    latitudes = np.round(map_latitude(city_data, np.array(latitudes)))
    longitudes = np.round(map_longitude(city_data, np.array(longitudes)))

    # The below is based off http://stackoverflow.com/questions/8647024/how-to-apply-a-disc-shaped-mask-to-a-numpy-array
    # Basically, we build a True/False mask (master_mask) the same size 
    # as the map. Each 'pixel' within the mask indicates whether the point 
    # is within provided distance from a car.
    # To build this, iterate over all cars and apply a circular mask of Trues
    # (circle_mask) around the point indicating each car. We'll need to shift 
    # things around near the borders of the map, but this is relatively
    # straightforward.

    time_preprocess_start = time.time()

    accessible_colour = (255, 255, 255, 0)  # white, fully transparent
    inaccessible_colour = (239, 239, 239, 100)  # #efefef, mostly transparent

    # not using accessible_multiplier currently because it's too slow
    # accessible_multiplier = (1, 1, 1, 0.6)
    # if using accessible_multiplier, 160 alpha for inaccessible looks better

    # generate basic background, for now uniformly indicating no cars available
    markers = np.empty(
        (city_data['MAP_SIZES']['MAP_Y'], city_data['MAP_SIZES']['MAP_X'], 4),
        dtype=np.uint8)
    markers[:] = inaccessible_colour  # can't use fill since it isn't a scalar

    # find distance radius, in pixels
    pixel_in_m = get_mean_pixel_size(city_data)
    radius = np.round(distance / pixel_in_m)

    # generate master availability mask
    master_mask = np.empty(
        (city_data['MAP_SIZES']['MAP_Y'], city_data['MAP_SIZES']['MAP_X']),
        dtype=np.bool)
    master_mask.fill(False)
    m_m_shape = master_mask.shape

    # generate basic circle mask
    y, x = np.ogrid[-radius: radius+1, -radius: radius+1]
    circle_mask = x**2+y**2 <= radius**2
    c_m_shape = circle_mask.shape

    timer.append((log_name + ': make_accessibility_background preprocess, ms',
                  (time.time()-time_preprocess_start)*1000.0))

    time_iter_start = time.time()

    for i in range(len(latitudes)):
        # to just crudely mark a square area around lat/lng:
        # markers[ (lat - radius) : (lat+radius), (lng-radius) : (lng+radius)] = accessible_colour

        # mask is drawn from top-left corner. to center mask around the point:
        x = latitudes[i] - radius
        y = longitudes[i] - radius

        # find various relevant locations within the matrix...

        # cannot give a negative number as first param in slice
        master_x_start = max(x, 0)
        master_y_start = max(y, 0)
        # but going over boundaries is ok, will trim automatically
        master_x_end = x + c_m_shape[0]
        master_y_end = y + c_m_shape[1]

        circle_x_start = 0
        circle_y_start = 0
        circle_x_end = c_m_shape[0]
        circle_y_end = c_m_shape[1]

        if x < 0:   # trim off left side
            circle_x_start = x * -1
        if y < 0:   # trim off top
            circle_y_start = y * -1
        if master_x_end > m_m_shape[0]:  # trim off right side
            circle_x_end = (m_m_shape[0] - master_x_end)
        if master_y_end > m_m_shape[1]:  # trim off bottom
            circle_y_end = (m_m_shape[1] - master_y_end)

        # make sure to OR the masks so that earlier circles' Trues 
        # aren't overwritten by later circles' Falses
        master_mask[
            master_x_start: master_x_end,
            master_y_start: master_y_end
            ] |= circle_mask[
                circle_x_start: circle_x_end,
                circle_y_start: circle_y_end]

        # not using accessible_multiplier currently because it's too slow
        # markers[master_mask] *= accessible_multiplier

    timer.append((log_name + ': make_accessibility_background mask iter, ms',
                  (time.time()-time_iter_start)*1000.0))

    time_mask_apply_start = time.time()

    # note: can also do something like this: markers[mask] *= (1, 1, 1, 0.5)
    # and it updates everything - should be useful for relative values.
    # except it has to happen within the iteration as shown above, and is also
    # pretty slow. like, adds 1.2 seconds per image slow. see if I can 
    # optimize it somehow, but multiplying a million-item array, even masked,
    # by a vector 200 times might just be inherently a bit slow :(

    markers[master_mask] = accessible_colour

    timer.append((log_name + ': make_accessibility_background mask apply, ms',
                  (time.time()-time_mask_apply_start)*1000.0))

    time_bg_render_start = time.time()

    timer.append((log_name + ': make_accessibility_background bg render, ms',
                  (time.time()-time_bg_render_start)*1000.0))

    return markers
