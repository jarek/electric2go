#!/usr/bin/env python2
# coding=utf-8

from datetime import timedelta
import time
import shutil
import matplotlib.pyplot as plt
import numpy as np
import Image

from city import CITIES, KNOWN_CITIES, is_latlng_in_bounds, get_mean_pixel_size


# speed ranges are designated as: 0-5; 5-15; 15-30; 30+
SPEED_CUTOFFS = [5, 15, 30, float('inf')]
SPEED_COLOURS = ['r', 'y', 'g', 'b']


timer = []


# strictly not correct as lat/lng isn't a grid, but close enough at city scales
def map_latitude(city, latitudes):
    city_data = CITIES[city]
    return ((latitudes - city_data['MAP_LIMITS']['SOUTH']) / \
        (city_data['MAP_LIMITS']['NORTH'] - city_data['MAP_LIMITS']['SOUTH'])) * \
        city_data['MAP_SIZES']['MAP_Y']

def map_longitude(city, longitudes):
    city_data = CITIES[city]
    return ((longitudes - city_data['MAP_LIMITS']['WEST']) / \
        (city_data['MAP_LIMITS']['EAST'] - city_data['MAP_LIMITS']['WEST'])) * \
        city_data['MAP_SIZES']['MAP_X']

def make_graph_axes(city, background = False, log_name = ''):
    """ Sets up figure area and axes for common properties for a city 
    to be graphed. The param `log_name` is used for logging only. """

    # set up figure area

    global timer

    time_plotsetup_start = time.time()

    dpi = 80
    # i actually have no idea why this is necessary, but the 
    # figure sizes are wrong otherwise. ???
    dpi_adj_x = 0.775
    dpi_adj_y = 0.8

    city_data = CITIES[city]

    # TODO: the two below take ~20 ms. try to reuse
    f = plt.figure(dpi=dpi)
    f.set_size_inches(city_data['MAP_SIZES']['MAP_X']/dpi_adj_x/dpi, \
            city_data['MAP_SIZES']['MAP_Y']/dpi_adj_y/dpi)

    # TODO: this takes 50 ms each time. try to reuse the whole set of axes
    # rather than regenerating it each time
    ax = f.add_subplot(111)
    ax.axis([0, city_data['MAP_SIZES']['MAP_X'], 0, city_data['MAP_SIZES']['MAP_Y']])

    # remove visible axes and figure frame
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)
    ax.set_frame_on(False)

    if isinstance(background, basestring) and os.path.exists(background):
        # matplotlib's processing makes the image look a bit worse than 
        # the original map - so keeping the generated graph transparent 
        # and overlaying it on source map post-render is a good option too
        background = plt.imread(background)

    if background:
        implot = ax.imshow(background, origin = 'lower', aspect = 'auto')

    timer.append((log_name + ': make_graph_axes, ms',
        (time.time()-time_plotsetup_start)*1000.0))

    return f,ax

def plot_points(ax, points, symbol):
    ys, xs, colours = zip(*points)
    colours = [colour + symbol for colour in colours]

    # see if there are different colours in the set, or if they're all the same
    same_colour = True
    first_colour = colours[0]
    for colour in colours:
        if colour != first_colour:
            same_colour = False
            break

    if same_colour:
        # if same colour, we can plot them all at once
        ax.plot(xs, ys, colours[0])
    else:
        # for now just plot each one separately. this isn't optimal but oh well
        for x,y,colour in zip(xs, ys, colours):
            ax.plot(x, y, colour)

    return ax

def plot_geopoints(ax, city, geopoints, symbol):
    lats, lngs, colours = zip(*geopoints)

    latitudes = map_latitude(city, np.array(lats))
    longitudes = map_longitude(city, np.array(lngs))

    return plot_points(ax, zip(latitudes, longitudes, colours), symbol)

def plot_lines(ax, lines_start_y, lines_start_x, lines_end_y, lines_end_x, colour = '#aaaaaa'):
    for i in range(len(lines_start_y)):
        l = plt.Line2D([lines_start_x[i], lines_end_x[i]], \
                [lines_start_y[i], lines_end_y[i]], color = colour)
        ax.add_line(l)

    return ax

def plot_geolines(ax, city, lines_start_lat, lines_start_lng, lines_end_lat, lines_end_lng, colour = '#aaaaaa'):
    # translate into map coordinates
    lines_start_y = map_latitude(city, np.array(lines_start_lat))
    lines_start_x = map_longitude(city, np.array(lines_start_lng))
    lines_end_y = map_latitude(city, np.array(lines_end_lat))
    lines_end_x = map_longitude(city, np.array(lines_end_lng))

    return plot_lines(ax, lines_start_y, lines_start_x, lines_end_y, lines_end_x, colour)

def plot_trips(ax, city, trips, colour = '#aaaaaa'):
    lines_start_lat = [t['from'][0] for t in trips]
    lines_start_lng = [t['from'][1] for t in trips]
    lines_end_lat = [t['to'][0] for t in trips]
    lines_end_lng = [t['to'][1] for t in trips]

    return plot_geolines(ax, city, lines_start_lat, lines_start_lng, lines_end_lat, lines_end_lng, colour)

def process_positions(city, positions, show_speeds=False, log_name=''):
    """
    extracts a list of all positions with colour to plot them with
    from a list of objects with metadata.
    :returns a list of lists formatted suitably for passing to plot_geopoints()
    """

    global timer

    time_process_start = time.time()

    processed_positions = []

    for position in positions:
        if is_latlng_in_bounds(city, position['coords']):
            if show_speeds and 'speed' in position['metadata']:
                # find the right speed basket
                for i in range(len(SPEED_CUTOFFS)):
                    if position['metadata']['speed'] < SPEED_CUTOFFS[i]:
                        position['coords'].append(SPEED_COLOURS[i])
                        break

            if len(position['coords']) == 2:
                # we're not classifying speeds, or speed not found in loop above
                position['coords'].append('b')

            processed_positions.append(position['coords'])

    timer.append((log_name + ': process_positions, ms',
        (time.time()-time_process_start)*1000.0))

    return processed_positions

def graph_wrapper(city, plot_function, image_name, background = False):
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
    f,ax = make_graph_axes(city, background, log_name)

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

def make_graph(city, positions, trips, first_filename, turn, second_filename = False,
    show_move_lines = True, show_speeds = False, symbol = '.',
    distance = False, time_offset = 0,
    **extra_args):
    """ Creates and saves matplotlib figure for provided positions and trips.
    If second_filename is specified, also copies the saved file to 
    second_filename. """

    global timer

    # use a different variable name for clarity where it'll be used only
    # for logging rather than actually accessing/creating files
    log_name = first_filename

    # load in vehicle positions in this time frame
    processed_positions = process_positions(city, positions, show_speeds, log_name)

    if distance:
        graph_background = make_accessibility_background(city, processed_positions, distance, log_name)
    else:
        graph_background = False

    # define what to add to the graph
    def plotter(f, ax):
        time_plot_start = time.time()

        # plot points for vehicles
        if len(processed_positions) > 0:
            ax = plot_geopoints(ax, city, processed_positions, symbol)

        # add in lines for moving vehicles
        if show_move_lines and len(trips) > 0:
            ax = plot_trips(ax, city, trips)

        # add labels
        city_data = CITIES[city]
        printed_time = turn + timedelta(0, time_offset*3600)

        coords = city_data['LABELS']['lines']
        fontsizes = city_data['LABELS']['fontsizes']

        ax.text(coords[0][0], coords[0][1],
            city_data['display'], fontsize = fontsizes[0])
        # prints something like "December 10, 2014"
        ax.text(coords[1][0], coords[1][1],
            '{d:%B} {d.day}, {d.year}'.format(d=printed_time), fontsize = fontsizes[1])
        # prints something like "Wednesday, 04:02"
        ax.text(coords[2][0], coords[2][1],
            '{d:%A}, {d:%H}:{d:%M}'.format(d=printed_time), fontsize = fontsizes[2])
        ax.text(coords[3][0], coords[3][1],
            'available cars: %d' % len(processed_positions), fontsize = fontsizes[3])

        timer.append((log_name + ': make_graph plot and label, ms',
            (time.time()-time_plot_start)*1000.0))

    # create and save plot
    image_first_filename = first_filename + '.png'
    graph_wrapper(city, plotter, image_first_filename, graph_background)

    # if requested, also copy with an iterative filename for ease of animation
    # copying the file rather than saving again is a lot faster
    if second_filename:
        shutil.copy2(image_first_filename, second_filename)

def make_positions_graph(city, positions, image_name):
    global timer

    time_positions_graph_start = time.time()

    def plotter(f, ax):
        processed = process_positions(city, positions, show_speeds=False, log_name=image_name)
        if len(processed) > 0:
            plot_geopoints(ax, city, processed, '.')

    graph_wrapper(city, plotter, image_name, background=False)

    timer.append((image_name + ': make_positions_graph total, ms',
        (time.time()-time_positions_graph_start)*1000.0))

def make_trips_graph(city, trips, image_name):
    global timer

    time_trips_graph_start = time.time()

    def plotter(f, ax):
        if len(trips) > 0:
            plot_trips(ax, city, trips)

    graph_wrapper(city, plotter, image_name, background=False)

    timer.append((image_name + ': make_trips_graph total, ms',
        (time.time()-time_trips_graph_start)*1000.0))

def make_accessibility_background(city, processed_positions, distance, log_name):
    global timer

    latitudes, longitudes, _colours = zip(*processed_positions)  # _colours not used
    latitudes = np.round(map_latitude(city, np.array(latitudes)))
    longitudes = np.round(map_longitude(city, np.array(longitudes)))

    # The below is based off http://stackoverflow.com/questions/8647024/how-to-apply-a-disc-shaped-mask-to-a-numpy-array
    # Basically, we build a True/False mask (master_mask) the same size 
    # as the map. Each 'pixel' within the mask indicates whether the point 
    # is within provided distance from a car.
    # To build this, iterate over all cars and apply a circular mask of Trues
    # (circle_mask) around the point indicating each car. We'll need to shift 
    # things around near the borders of the map, but this is relatively
    # straighforward.

    time_preprocess_start = time.time()

    accessible_colour = (255, 255, 255, 0) # white, fully transparent
    accessible_multiplier = (1, 1, 1, 0.6)
    # if using accessible_multiplier, 160 alpha for inaccessible looks better
    inaccessible_colour = (239, 239, 239, 100) # #efefef, mostly transparent

    city_data = CITIES[city]

    # generate basic background, for now uniformly indicating no cars available
    markers = np.empty(
        (city_data['MAP_SIZES']['MAP_Y'], city_data['MAP_SIZES']['MAP_X'], 4),
        dtype = np.uint8)
    markers[:] = inaccessible_colour # can't use fill since it isn't a scalar

    # find distance radius, in pixels
    pixel_in_m = get_mean_pixel_size(city)
    radius = np.round(distance / pixel_in_m)

    # generate master availability mask
    master_mask = np.empty(
        (city_data['MAP_SIZES']['MAP_Y'], city_data['MAP_SIZES']['MAP_X']),
        dtype = np.bool)
    master_mask.fill(False)
    m_m_shape = master_mask.shape

    # generate basic circle mask
    y,x = np.ogrid[-radius: radius+1, -radius: radius+1]
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
        if master_x_end > m_m_shape[0]: # trim off right side
            circle_x_end = (m_m_shape[0] - master_x_end)
        if master_y_end > m_m_shape[1]: # trim off bottom
            circle_y_end = (m_m_shape[1] - master_y_end)

        # make sure to OR the masks so that earlier circles' Trues 
        # aren't overwritten by later circles' Falses
        master_mask[
            master_x_start : master_x_end, 
            master_y_start : master_y_end
            ] |= circle_mask[
                circle_x_start : circle_x_end, 
                circle_y_start : circle_y_end]

        #markers[master_mask] *= accessible_multiplier
        #master_mask.fill(False)

        #end for

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

    created_background = Image.fromarray(markers, 'RGBA')

    timer.append((log_name + ': make_accessibility_background bg render, ms',
        (time.time()-time_bg_render_start)*1000.0))

    return created_background
