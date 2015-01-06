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

    ax.plot(xs, ys, colours)

    return ax

def plot_geopoints(ax, city, geopoints, symbol):
    lats, lngs, colours = zip(*geopoints)

    latitudes = map_latitude(city, lats)
    longitudes = map_longitude(city, lngs)

    return plot_points(ax, zip(latitudes, longitudes, colours), symbol)

def plot_lines(ax, lines_start_y, lines_start_x, lines_end_y, lines_end_x, color = '#aaaaaa'):
    for i in range(len(lines_start_y)):
        l = plt.Line2D([lines_start_x[i], lines_end_x[i]], \
                [lines_start_y[i], lines_end_y[i]], color = color)
        ax.add_line(l)

    return ax

def plot_geolines(ax, city, lines, color = '#aaaaaa'):
    lines_start_lat, lines_start_lng, lines_end_lat, lines_end_lng = zip(*lines)

    # translate into map coordinates
    lines_start_y = map_latitude(city, np.array(lines_start_lat))
    lines_start_x = map_longitude(city, np.array(lines_start_lng))
    lines_end_y = map_latitude(city, np.array(lines_end_lat))
    lines_end_x = map_longitude(city, np.array(lines_end_lng))

    return plot_lines(ax, lines_start_y, lines_start_x, lines_end_y, lines_end_x, color)

def make_graph_object(data, city, turn, show_move_lines = True, \
    show_speeds = False, symbol = '.', log_name = '', background = False,
    time_offset = 0,
    **extra_args):
    """ Creates and returns the matplotlib figure for the provided data.
    The param `log_name` is used for logging only. """

    args = locals()

    # my lists of latitudes, longitudes, will be at most
    # as long as data (when all cars are currently being seen)
    # and usually around 1/2 - 2/3rd the size. pre-allocating 
    # zeros and keeping track of the actual size is the most 
    # memory-efficient thing to do, i think.
    # (I have to use numpy arrays to transform coordinates. 
    # and numpy array appends are not in place.)
    global timer
    time_init_start = time.time()

    max_length = len(data)

    latitudes = np.empty(max_length)
    longitudes = np.empty(max_length)
    
    # lists for the lines will be usually 5-30 long or so. 
    # i'll keep them as standard python for the appends 
    # and convert later
    lines_start_lat = []
    lines_start_lng = []
    lines_end_lat = []
    lines_end_lng = []

    speeds = []
    for i in range(len(SPEED_CUTOFFS)):
        # create the necessary amount of [lat, lng] baskets
        speeds.append( [ [], [] ] )

    car_count = 0

    timer.append((log_name + ': make_graph init, ms',
        (time.time()-time_init_start)*1000.0))

    time_load_start = time.time()

    for car in data:
        if data[car]['seen'] == turn or data[car]['just_moved']:
            # The second condition is for buses, where positions
            # are not logged exactly on the turn. 
            # Since they're pretty much continuously moving except
            # in really really bad traffic, this is an acceptable
            # workaround.
            # Note that cars that aren't moving have just_moved 
            # set to false in process_data.
            if is_latlng_in_bounds(city, data[car]['coords']):
                latitudes[car_count] = data[car]['coords'][0]
                longitudes[car_count] = data[car]['coords'][1]

                if 'speed' in data[car]:
                    # find the right speed basket
                    i = 0
                    while i < len(speeds):
                        if data[car]['speed'] < SPEED_CUTOFFS[i]:
                            speeds[i][0].append(data[car]['coords'][0])
                            speeds[i][1].append(data[car]['coords'][1])
                            i = len(speeds) # break loop
                        else:
                            i = i + 1

            car_count = car_count + 1

            # if car has just moved, add a line from previous point to current point
            if data[car]['just_moved'] == True:
                lines_start_lat.append(data[car]['prev_coords'][0])
                lines_start_lng.append(data[car]['prev_coords'][1])
                lines_end_lat.append(data[car]['coords'][0])
                lines_end_lng.append(data[car]['coords'][1])

    timer.append((log_name + ': make_graph load, ms',
        (time.time()-time_load_start)*1000.0))

    f,ax = make_graph_axes(city, background, log_name)

    time_plot_start = time.time()

    if show_speeds is False:
        #ax.plot(longitudes, latitudes, 'b' + symbol)
        ax = plot_geopoints(ax, city, zip(latitudes, longitudes, 'b' * len(latitudes)), symbol)
    else:
        for i in range(len(speeds)):
            # TODO: try to plot those with on bottom, under newer 
            # points. might require changes a couple of lines above
            # instead. reverse alphabetical sort by key?

            # note this syntax only works when SPEED_COLOURS are one-character strings
            ax = plot_geopoints(ax, city, zip(speeds[i][0], speeds[i][1], SPEED_COLOURS * len(speeds[i])), symbol)

    # add in lines for moving vehicles
    if show_move_lines:
        ax = plot_geolines(ax, city, zip(lines_start_lat, lines_start_lng, lines_end_lat, lines_end_lng))

    city_data = CITIES[city]

    # add labels
    printed_time = turn + timedelta(0, time_offset*3600)
    if 'fontsizes' in city_data['LABELS']:
        # gradual transition to new labelling format - only for cities 
        # that have fontsizes array defined

        coords = city_data['LABELS']['lines']
        fontsizes = city_data['LABELS']['fontsizes']

        ax.text(coords[0][0], coords[0][1], 
            city_data['display'], fontsize = fontsizes[0])
        ax.text(coords[1][0], coords[1][1],
            printed_time.strftime('%B %d, %Y').replace(' 0',' '),
            fontsize = fontsizes[1])
        # the .replace gets rid of leading zeros in day numbers.
        # it's a bit of a hack but it works with no false positives
        # until we get a year beginning with a zero, which shouldn't be 
        # a problem for a while
        ax.text(coords[2][0], coords[2][1], 
            printed_time.strftime('%A, %H:%M'), fontsize = fontsizes[2])
        ax.text(coords[3][0], coords[3][1], 
            'available cars: %d' % car_count, fontsize = fontsizes[3])
        # TODO: maybe have an option to include this
        #ax.text(coords[4][0], coords[4][1], 'moved this round: %d' % 
        #    len(lines_start_lat), fontsize = fontsizes[4])
    else:
        fontsize = city_data['LABELS']['fontsize']
        ax.text(city_data['LABELS']['lines'][0][0], city_data['LABELS']['lines'][0][1], \
            city_data['LABELS']['display'] + ' ' + \
            printed_time.strftime('%Y-%m-%d %H:%M'), fontsize=fontsize)
        ax.text(city_data['LABELS']['lines'][1][0], city_data['LABELS']['lines'][1][1], \
            'available cars: %d' % car_count, fontsize=fontsize)
        ax.text(city_data['LABELS']['lines'][2][0], city_data['LABELS']['lines'][2][1], \
            'moved this round: %d' % len(lines_start_lat), fontsize=fontsize)

    timer.append((log_name + ': make_graph plot, ms',
        (time.time()-time_plot_start)*1000.0))

    return f,ax

def make_graph(data, city, first_filename, turn, second_filename = False, \
    show_move_lines = True, show_speeds = False, symbol = '.', \
    background = False, time_offset = 0, \
    **extra_args):
    """ Creates and saves matplotlib figure for provided data. 
    If second_filename is specified, also copies the saved file to 
    second_filename. """

    args = locals()

    global timer

    time_total_start = time.time()

    # use a different variable name for clarity where it'll be used only
    # for logging rather than actually accessing/creating files
    log_name = first_filename
    args['log_name'] = first_filename

    f,ax = make_graph_object(**args)

    time_save_start = time.time()

    # saving as .png takes about 130-150 ms
    # saving as .ps or .eps takes about 30-50 ms
    # .svg is about 100 ms - and preserves transparency
    # .pdf is about 80 ms
    # svg and e/ps would have to be rendered before being animated, though
    # possibly making it a moot point
    image_first_filename = first_filename + '.png'
    f.savefig(image_first_filename, bbox_inches='tight', pad_inches=0, 
        dpi=80, transparent=True)

    # if requested, also save with iterative filenames for ease of animation
    if not second_filename == False:
        # copying the file rather than saving again is a lot faster
        shutil.copyfile(image_first_filename, second_filename)

    # close the plot to free the memory. memory is never freed otherwise until
    # script is killed or exits.
    # this line causes a matplotlib backend RuntimeError in a close_event()
    # function ("wrapped C/C++ object of %S has been deleted") in every second
    # iteration, but this appears to be async from main thread and 
    # doesn't appear to influence the correctness of output, 
    # so I'll leave it as is for the time being
    plt.close(f)

    timer.append((log_name + ': make_graph save, ms',
        (time.time()-time_save_start)*1000.0))

    timer.append((log_name + ': make_graph total, ms',
        (time.time()-time_total_start)*1000.0))

def make_accessibility_graph(data, city, first_filename, turn, distance, \
    second_filename = False, show_move_lines = True, show_speeds = False, \
    symbol = '.', time_offset = 0, **extra_args):

    args = locals()

    global timer

    time_total_start = time.time()

    # use a different variable name for clarity where it'll be used only
    # for logging rather than actually accessing/creating files
    log_name = first_filename
    args['log_name'] = first_filename

    time_data_read_start = time.time()

    # TODO: strictly speaking the iteration over data is copied and duplicated 
    # from make_graph_object(). The perf penalty is unlikely to be large, but
    # maintenance might be a pain should I want to change it in 
    # make_graph_object(). So try to reorganize code to fix any duplications.

    max_length = len(data)
    car_count = 0
    latitudes = np.empty(max_length)
    longitudes = np.empty(max_length)

    for car in data:
        if data[car]['seen'] == turn or data[car]['just_moved']:
            if is_latlng_in_bounds(city, data[car]['coords']):
                latitudes[car_count] = data[car]['coords'][0]
                longitudes[car_count] = data[car]['coords'][1]

                car_count += 1

    latitudes = np.round(map_latitude(city, latitudes[:car_count]))
    longitudes = np.round(map_longitude(city, longitudes[:car_count]))

    timer.append((log_name + ': make_accessibility_graph data read, ms',
        (time.time()-time_data_read_start)*1000.0))

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

    timer.append((log_name + ': make_accessibility_graph masks preprocess, ms',
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

    timer.append((log_name + ': make_accessibility_graph mask iter, ms',
        (time.time()-time_iter_start)*1000.0))

    time_mask_apply_start = time.time()

    # note: can also do something like this: markers[mask] *= (1, 1, 1, 0.5)
    # and it updates everything - should be useful for relative values.
    # except it has to happen within the iteration as shown above, and is also
    # pretty slow. like, adds 1.2 seconds per image slow. see if I can 
    # optimize it somehow, but multiplying a million-item array, even masked,
    # by a vector 200 times might just be inherently a bit slow :(

    markers[master_mask] = accessible_colour

    timer.append((log_name + ': make_accessibility_graph mask apply, ms',
        (time.time()-time_mask_apply_start)*1000.0))

    time_bg_render_start = time.time()

    args['background'] = Image.fromarray(markers, 'RGBA')

    timer.append((log_name + ': make_accessibility_graph bg render, ms',
        (time.time()-time_bg_render_start)*1000.0))

    make_graph(**args)

    timer.append((log_name + ': make_accessibility_graph total, ms',
        (time.time()-time_total_start)*1000.0))

