import numpy as np
from copy import deepcopy
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from tkinter import *
from matplotlib import colors
import time

def plot_t_grid(temp_grid):
    """Plots the current state of the temp_grid (values from source only)

    Args:
        temp_grid (3d numpy array): previous x, previous y, and current value for each tile
    """
    new_grid = []
    for i in range(len(temp_grid)):
        for j in range(len(temp_grid[0])):
            new_grid.append(temp_grid[i][j][2])
    new_grid = np.asarray(new_grid)
    new_grid = np.reshape(new_grid, (len(temp_grid), len(temp_grid[0])))
    print(new_grid)

def plot_grid(grid_n):
    plt.imshow(grid_n, interpolation='none')
    plt.show()
    plt.clf()

def a_init_aStar(data):
    """Initializes the a_star grid

    Args:
        grid (numpy array): grid with barriers

    Returns:
        numpy array: grid with room for x, y, and manhattan distance
                     of previous tile
    """
    width, height = data[0].split(" ")
    width = int(width)
    height = int(height)

    # 3 because x prev, y prev, manhattan distance
    temp_grid = np.zeros((height, width, 3))
    perm_grid = np.zeros((height, width))

    # separating out the input obstructions
    num_obstructions = int(data[1])
    obstructions = []

    # plus 2 because of the data offset in the input file
    for i in range(2, num_obstructions+2):
        temp = data[i].split()
        obstructions.append(temp)

    obstructions = np.asarray(obstructions)

    wire_location = num_obstructions+2

    num_wires = int(data[wire_location])

    wires_temp = data[wire_location+1:]

    # separating out the wires
    wires = []
    for i in range(num_wires):
        temp = wires_temp[i].split()
        wires.append(temp)
        num_pins = wires[i][0]
        for j in range(int(num_pins)):
            x = int(wires[i][1 + (int)(j) * 2])
            y = int(wires[i][2 + (int)(j) * 2])
            perm_grid[y][x] = (-1)* (i + 2)
    for i in range(num_obstructions):
        perm_grid[int(obstructions[i][1])][int(obstructions[i][0])] = -1

    return perm_grid, temp_grid, wires, num_wires

def a_manhattan_distance(loc1, loc2):
    """Finds the manhattan distances between 2 points

    Args:
        loc1 (numpy array): source coordinates
        loc2 (numpy array): sink coordinates

    Returns:
        int: manhattan distance
    """
    x = (abs(int(loc1[0]) - int(loc2[0])) + abs(int(loc1[1]) - int(loc2[1])))
    #print("man_dist: " + str(x))
    return x

def a_adjacent(t_grid, x, y, value, sink, source, loc_dict, perm_grid, wire, all_sinks, connection, connection_location):
    """Looks at adjacent tiles, based on the highest priority element (lowest key value) in the priority queue.
       Capable of finding a previously placed wire on the same net.

    Args:
        t_grid (3d numpy array): previous x, previous y, and current value for each tile
        x (int): x coord of current tile
        y (int): y coord of current tile
        value (int): man. distance from source
        sink (numpy array): the current sink we're solving for
        source (numpy array): source x, y coords
        loc_dict (dictionary): dictonary containing the keys as man. distances, and the (x, y)'s at the given key
        perm_grid (numpy array): grid containing placed wires + blocks
        wire (int): the wire number
        all_sinks (numpy array): list of all sinks
        connection (numpy array): man. value of closest tile to given sink
        connection_location (numpy array): where connection values are located (within 1 tile of all_sinks values)

    Returns:
        t_grid (3d numpy array): previous x, previous y, and current value for each tile
        loc_dict (dictionary): dictonary containing the keys as man. distances, and the (x, y)'s at the given key
        wire_found (boolean): did we find a previously placed wire on the same net?
        connection (numpy array): man. value of closest tile to given sink
        connection_location (numpy array): where connection values are located (within 1 tile of all_sinks values)

    """

    wire_found = False
    wire_value = -1 * (2 + wire)

    # if we've arrived at a wire that has already been placed, and it's not a sink
    if ( (x + 1) < t_grid.shape[1] and perm_grid[y][x + 1] == wire_value and not is_sink(x+1, y, all_sinks) ):
        wire_found = True
        value = a_manhattan_distance([x + 1, y], source) + a_manhattan_distance([x + 1, y], sink)
        t_grid[y][x + 1] = [x, y, value]
        connection[0] = value
        connection_location[0] = [x, y]

    if( (x - 1) >= 0 and perm_grid[y][x - 1] == wire_value and not is_sink(x-1, y, all_sinks)):
        wire_found = True
        value = a_manhattan_distance([x - 1, y], source) + a_manhattan_distance([x - 1, y], sink)
        t_grid[y][x - 1] = [x, y, value]
        connection[0] = value
        connection_location[0] = [x, y]

    if( (y + 1) < t_grid.shape[0] and perm_grid[y + 1][x] == wire_value and not is_sink(x, y + 1, all_sinks)):
        wire_found = True
        value = a_manhattan_distance([x, y + 1], source) + a_manhattan_distance([x, y + 1], sink)
        connection[0] = value
        connection_location[0] = [x, y]
        t_grid[y + 1][x] = [x, y, value]

    if( (y - 1) >= 0 and perm_grid[y - 1][x] == wire_value and not is_sink(x, y - 1, all_sinks)):
        wire_found = True
        value = a_manhattan_distance([x, y - 1], source) + a_manhattan_distance([x, y - 1], sink)
        connection[0] = value
        connection_location[0] = [x, y]
        t_grid[y - 1][x] = [x, y, value]

    # if we found a wire, we don't need to look at any other values in the priority queue.
    if (wire_found):
        for i in range(int(len(all_sinks) / 2)):
            x_t = int(all_sinks[int(i) * 2])
            y_t = int(all_sinks[1 + int(i) * 2])
            perm_grid[y_t][x_t] = wire_value
        return np.asarray(t_grid), loc_dict, wire_found, connection, connection_location
    
    # if the point is in bounds, if it's unoccupied, and if it has the same or less manhattan distance
    if( (x + 1) < t_grid.shape[1] and t_grid[y][x + 1][2] == 0 and perm_grid[y][x + 1] > -1):
        value = a_manhattan_distance([x + 1, y], source) + a_manhattan_distance([x + 1, y], sink)
        t_grid[y][x + 1] = [x, y, value]
        if (value in loc_dict):
            loc_dict[value].append(x+1)
            loc_dict[value].append(y)
        else:
            loc_dict[value] = [x+1, y]

    if( (x - 1) >= 0 and t_grid[y][x - 1][2] == 0 and perm_grid[y][x - 1] > -1):
        value = a_manhattan_distance([x - 1, y], source) + a_manhattan_distance([x - 1, y], sink)
        t_grid[y][x - 1] = [x, y, value]
        if (value in loc_dict):
            loc_dict[value].append(x-1)
            loc_dict[value].append(y)
        else:
            loc_dict[value] = [x-1, y]

    if( (y + 1) < t_grid.shape[0] and t_grid[y + 1][x][2] == 0 and perm_grid[y + 1][x] > -1):
        value = a_manhattan_distance([x, y + 1], source) + a_manhattan_distance([x, y + 1], sink)
        t_grid[y + 1][x] = [x, y, value]
        if (value in loc_dict):
            loc_dict[value].append(x)
            loc_dict[value].append(y+1)
        else:
            loc_dict[value] = [x, y+1]

    if( (y - 1) >= 0 and t_grid[y - 1][x][2] == 0 and perm_grid[y - 1][x] > -1):
        value = a_manhattan_distance([x, y - 1], source) + a_manhattan_distance([x, y - 1], sink)
        t_grid[y - 1][x] = [x, y, value]
        if (value in loc_dict):
            loc_dict[value].append(x)
            loc_dict[value].append(y-1)            
        else:
            loc_dict[value] = [x, y-1]
    
    for i in range(int(len(all_sinks) / 2)):
            x_t = int(all_sinks[int(i) * 2])
            y_t = int(all_sinks[1 + int(i) * 2])
            perm_grid[y_t][x_t] = wire_value
    return np.asarray(t_grid), loc_dict, wire_found, connection, connection_location

def is_sink(x, y, sinks):
    for i in range(int(len(sinks) / 2)):
        sink_loc = [sinks[i * 2], sinks[i * 2 + 1]]
        if ([x, y] == sink_loc):
            return True
    return False
# shouldn't need to modify this one too much. might need to check for the lowest value one,
# but I don't think so.
def a_found_sink(t_grid, found_connection, source, con_loc):
    """looks for sinks in adjacent squares at the current grid tile
       Used in the forward pass

    Args:
        t_grid (numpy array): grid with the distances from the source
        found_connection (numpy array): value at the found connection
        x (int): x coordinate of current grid tile
        y (int): y coordinate of current grid tile
        j (int): the number of the sink we're looking at
        con_loc (np array): the tile of the found connection

    Returns:
        connection_location [numpy array]: location of the tile closest to the sink (if connected to net)
        found_connection [int]: value of the tile closest to the sink (if connected to net)
        boolean: if we have found all of the sinks
    """
    x, y = source

    #hacky way to make sure that we got the working grid slot..
    found_val = 0

    # if we have a valid point, and if it's been visited by the adjacent algorithm
    # (known distance from source)
    if( (x + 1) < t_grid.shape[1] and t_grid[y][x + 1][2] > 0):
        found_connection[0] = t_grid[y][x + 1][2]
        con_loc[0] = [x + 1, y]
        found_val = found_connection[0]
    elif( (x - 1) >= 0 and t_grid[y][x - 1][2] > found_val):
        found_connection[0] = t_grid[y][x - 1][2]
        con_loc[0] = [x - 1, y]
        found_val = found_connection[0]
    elif( (y + 1) < t_grid.shape[0] and t_grid[y + 1][x][2] > found_val):
        found_connection[0] = t_grid[y + 1][x][2]
        con_loc[0] = [x, y + 1]
        found_val = found_connection[0]
    elif( (y - 1) >= 0 and t_grid[y - 1][x][2] > found_val):
        found_connection[0] = t_grid[y - 1][x][2]
        con_loc[0] = [x, y - 1]

    return con_loc, found_connection, found_connection[0] > 0

def a_backtrace(t_grid, perm_grid, sink_locations, wire_num, all_sinks, num_wires, figure, ax):
    
    """Traces from the source to the value nearest to the current sink.

    Args:
        t_grid (3d numpy array): previous x, previous y, and current value for each tile
        perm_grid (numpy array): grid containing placed wires + blocks
        sink_locations ([type]): [description]
        wire_num (int): the wire number
        all_sinks (numpy array): list of all sinks

    Returns:
        perm_grid (numpy array): grid containing placed wires + blocks
    """

    cmap = colors.ListedColormap(['white', 'blue', 'purple', 'yellow', 'cyan', 'black'], N=num_wires + 2)
    bounds = []
    for i in range(-1, num_wires + 2):
        bounds.append(i + .1)
    norm = colors.BoundaryNorm(bounds, cmap.N)
    ax.imshow(perm_grid, cmap=cmap, norm=norm)
    plt.xlabel("X Location", fontsize = 18)
    plt.ylabel("Y Location", fontsize = 18)
    ax.grid(which='major', axis='both', linestyle='-', color='k', linewidth=2)

    # print("entering backtrace...")

    # print(sink_locations)
    wire_value = -1 * (wire_num + 2)
    # plot_t_grid(t_grid)
    

    # for each sink
    x = int(sink_locations[0])
    y = int(sink_locations[1])
    prev_coords = [-1, -1]

    # avoid connections only between sinks - need to connect to source
    # for i in range(int(len(all_sinks) / 2)):
    #     if (int(i) == wire_num):
    #         continue
    #     x_t = int(all_sinks[int(i) * 2])
    #     y_t = int(all_sinks[1 + int(i) * 2])
    #     perm_grid[y_t][x_t] = 0

    # plot_grid(perm_grid)
    while True:
        ax.imshow(perm_grid * -1, cmap=cmap, norm=norm)
        figure.canvas.draw()
        figure.canvas.flush_events()
        # time.sleep(0.1)
        # if we've reached a wire
        # The or statement covers the corner case of if we are looking at a sink that had been traced over 
        # by a previous wire. The temp grid will have location 0, 0 stored at it. This covers the corner case 
        # if we have to go through the point at 0, 0 and it is a sink.
        if(perm_grid[y][x] == wire_value or (t_grid[y][x][2] == 0 and prev_coords != [0, 1] and prev_coords != [1, 0])): 
            for i in range(int(len(all_sinks) / 2)):
                x_t = int(all_sinks[int(i) * 2])
                y_t = int(all_sinks[1 + int(i) * 2])
                perm_grid[y_t][x_t] = wire_value
            break
        else:
            perm_grid[y][x] = wire_value
            prev_coords = [x, y]
            x, y = t_grid[y][x][:2]
            x = int(x)
            y = int(y)
    for i in range(int(len(all_sinks) / 2)):
        x_t = int(all_sinks[int(i) * 2])
        y_t = int(all_sinks[1 + int(i) * 2])
        perm_grid[y_t][x_t] = wire_value
    return perm_grid

def a_solve(perm_grid, temp_grid, wires, num_wires):
    """Solves a net using the A* algorithm to find connections between a wire source and 
       its associated sinks.

    Args:
        perm_grid (numpy array): grid containing placed wires + blocks
        t_grid (numpy array): grid with the distances from the source, and the x, y coord of prev. tile
        wires (numpy array): list of wires and the associated sinks / sources
        num_wires (int): number of wires

    Returns:
        perm_grid (numpy array): grid containing placed wires + blocks with newly placed net
    """
    plt.ion()
    figure, ax = plt.subplots(figsize=(len(perm_grid),len(perm_grid[0])))
    for wire in range(num_wires):
        sinks_found = False
        wire_found = False
        source = wires[wire][1:3]
        source = [int(i) for i in source]
        all_sinks = wires[wire][3:]
        all_sinks = [int(i) for i in all_sinks]
        
        # first pin is a source
        for sink in range (int(wires[int(wire)][0]) - 1):
            # used to keep track of if we have a connection between the new "path"
            # of values between the souce and the sink. Stores the numerical value
            # of the first grid location that arrives adjacent to the pin in question
            connection = np.zeros((1, 1))

            # Keeps track of the location (x, y) of each saved connection
            connection_location = np.zeros((1, 2))
            temp_grid[temp_grid > 0] = 0
            this_sink = wires[wire][3 + 2 * int(sink): 5 + 2 * int(sink)]
            this_sink = [int(i) for i in this_sink]

            d_key = a_manhattan_distance(source, this_sink)

            updated_locations = {d_key: deepcopy(this_sink)}

            # print("This Sink")
            # print(this_sink)
            # print(source)
            # print(updated_locations)

            while connection[0] == 0:
                # print("updated locations")
                # print(updated_locations)
                # if we have to change the value of the key and move away from the optimal path
                if not updated_locations[d_key]:
                    del updated_locations[d_key]
                if not updated_locations:
                    print("Wire " + str(sink) + " not found.")
                    break
                else:
                    # retrives the minimum key
                    d_key = min(updated_locations)

                x = updated_locations[d_key][0]
                y = updated_locations[d_key][1]

                man_dist = a_manhattan_distance(source, [x, y]) + a_manhattan_distance(this_sink, [x, y])

                temp_grid, updated_locations, wire_found, connection, connection_location = a_adjacent(temp_grid, x, y, man_dist, this_sink, source, updated_locations, perm_grid, int(wire), all_sinks, connection, connection_location)
                # remove the point we just searched at
                del updated_locations[d_key][:2]
                if(wire_found):
                    perm_grid = a_backtrace(temp_grid, perm_grid, connection_location[0], int(wire), all_sinks, num_wires, figure, ax)
                    # print(perm_grid)
                    break

                # bring the lowest manhattan distances to the front
                connection_location, connection, sinks_found = a_found_sink(temp_grid, connection, source, connection_location)
                # print("Sinks found: " + str(sinks_found))
                # print("connection")
                # print(connection)
                # print("connection location:")
                # print(connection_location[0])
                
                if(sinks_found):
                    perm_grid = a_backtrace(temp_grid, perm_grid, connection_location[0], int(wire), all_sinks, num_wires, figure, ax)
                    # print(perm_grid)

    return perm_grid