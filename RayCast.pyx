"""
##############################################################################################################
@author Álvaro Fernández García
@version 1.4
@date 4, feb, 2019

A Ray-casting 2D render engine based on python3 and pyglet.
Inspired in retro FPS games.
This module implements the RayCasting using Cython for greater efficiency in calculations.
##############################################################################################################
"""

from libc.math cimport tan, abs, cos, ceil, sqrt


##############################################################################################################


cdef float check_horizontal_intersections(float alpha, float px, float py, int ncols, int nrows, \
    float csize, world):
    """
    Return the squared distance from player to an horizontal
    cell line wich is labeled as wall.
    Return -1 if there isn't collision.
    (Note) It is considered that an horizontal line belongs to its upper cell if 
    ray goes up, and to its lower cell if ray goes down.
    """
    
    cdef float Y = 0.0
    cdef float Y_inc = 0.0
    cdef float X = 0.0
    cdef float X_inc = 0.0
    cdef float PI = 3.14159265

    # Get first point Y coordinate and y_inc
    # If raycast is pointing up:   
    if 0.0 <= alpha and alpha < 180.0:
        Y = (py // csize) * csize - 1.0 # Math trick for acomplish (Note)
        Y_inc = -csize
    else:
        Y = (py // csize) * csize + csize # Math trick for acomplish (Note)
        Y_inc = csize

    # Get first point X coordinate and x_inc:
    cdef float div = tan(alpha*PI/180)
    if div != 0:
        X = px + (py - Y) / div
        X_inc = abs(csize / div)
    else:
        X = px + (py - Y) / 0.000001
        X_inc = csize / 0.000001 

    if 90.0 <= alpha and alpha < 270.0:
        X_inc = -X_inc

    # Repeat until we found a wall:
    while 0.0 <= (X // csize) and (X // csize) < ncols and 0 <= (Y // csize) and (Y // csize) < nrows:  
        if world[int(Y // csize)][int(X // csize)] == "W":
            return (px - X)**2 + (py - Y)**2
        else:
            X += X_inc
            Y += Y_inc

    return -1.0


##############################################################################################################


cdef float check_vertical_intersections(float alpha, float px, float py, int ncols, int nrows, \
    float csize, world):
    """
    Return the squared distance from player to a vertical
    cell line wich is labeled as wall.
    Return -1 if there isn't collision.
    (Note) It is considered that a vertical line belongs to its left cell 
    if ray goes left, and to its right cell if ray goes right.
    """
    
    cdef float Y = 0.0
    cdef float Y_inc = 0.0
    cdef float X = 0.0
    cdef float X_inc = 0.0
    cdef float PI = 3.14159265

    # Get first point X coordinate and x_inc
    # If raycast is pointing left:   
    if 90.0 <= alpha and alpha < 270.0:
        X = (px // csize) * csize - 1.0 # Math trick for acomplish (Note)
        X_inc = -csize
    else:
        X = (px // csize) * csize + csize # Math trick for acomplish (Note)
        X_inc = csize

    # Get first point Y coordinate and Y_inc:
    Y = py + (px - X) * tan(alpha*PI/180)
    Y_inc = abs(csize * tan(alpha*PI/180))

    if 0.0 <= alpha and alpha < 180.0:
        Y_inc = -Y_inc

    # Repeat until we found a wall:
    while 0.0 <= (X // csize) and (X // csize) < ncols and 0 <= (Y // csize) and (Y // csize) < nrows:  
        if world[int(Y // csize)][int(X // csize)] == "W":
            return (px - X)**2 + (py - Y)**2
        else:
            X += X_inc
            Y += Y_inc

    return -1.0


##############################################################################################################


cpdef cast_rays(float px, float py, float alpha, int ncols, int nrows, float csize, world, int fov, \
    float proj_const, int pp_width, float angle_btw_rc):
    """
    Cast rays along player's field of view and return a list of
    triplets of slice height, viewport fringe and distance.
    """

    out = []
    cdef float angle = alpha + (fov >> 1)
    cdef float hor = 0.0
    cdef float ver = 0.0
    cdef float tmp = 0.0
    cdef float PI = 3.14159265
    cdef float dst = 0.0
    cdef float correct = 0.0

    for i in range(pp_width):
        hor = check_horizontal_intersections(angle, px, py, ncols, nrows, csize, world)
        ver = check_vertical_intersections(angle, px, py, ncols, nrows, csize, world)
        
        if ver < 0 and hor < 0:
            continue

        # Get min:
        if ver < 0:
            tmp = hor
        elif hor < 0:
            tmp = ver
        else:
            if ver < hor:
                tmp = ver
            else:
                tmp = hor
        
        # This perspective correction is used to fix fishbowl effect:
        correct = cos((angle - alpha)*PI/180)
        dst = sqrt(tmp) * correct
        # Use similar triangle equation for compute slice height:
        out.append((int(ceil(proj_const / dst)), i, dst))
        
        angle = (angle - angle_btw_rc) % 360.0
    
    return out