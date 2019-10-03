# -*- coding: utf-8 -*-

"""
##############################################################################################################
@author Álvaro Fernández García
@version 1.4
@date 4, feb, 2019

A Ray-casting 2D render engine based on python3 and pyglet.
Inspired in retro FPS games.

References: 
https://permadi.com/1996/05/ray-casting-tutorial-table-of-contents
https://pyglet.readthedocs.io/en/pyglet-1.3-maintenance/programming_guide/quickstart.html
##############################################################################################################
"""

import itertools
import sys
import math
import pyglet
import inspect
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pyximport; pyximport.install()
import RayCast

##############################################################################################################

class Player:
    """
    Object of type player/first person camera. 
    Public attributes:
    * x -- Player's X coordinate (with (0,0) in screen upper-left corner)
    * y -- Player's y coordinate (with (0,0) in screen upper-left corner)
    * alpha -- Angle of view (in degrees)
    * SPEED -- Player's velocity (in units per update)
    * CAMERA_SPEED -- Player's camera rotation velocity (in degrees per 
    update)
    * FOV -- Field of view (in degrees) 60 by default (Recommended not 
    to change it)
    """

    def __init__(self, x=0, y=0, alpha=90, speed=300, camera_speed=100):
        self.x = x
        self.y = y
        self.alpha = alpha
        self.SPEED = speed
        self.CAMERA_SPEED = camera_speed
        self.FOV = 60

    
    def move_forward(self, dt):
        """
        Moves player forward.
        dt -- delta time
        """
        self.y -= self.SPEED * math.sin(math.radians(self.alpha)) * dt
        self.x += self.SPEED * math.cos(math.radians(self.alpha)) * dt


    def move_backward(self, dt):
        """
        Moves player backward.
        dt -- delta time
        """
        self.y += self.SPEED * math.sin(math.radians(self.alpha)) * dt
        self.x -= self.SPEED * math.cos(math.radians(self.alpha)) * dt


    def rotate_left(self, dt):
        """
        Rotates camera to left.
        dt -- delta time
        """
        self.alpha = (self.alpha + (self.CAMERA_SPEED * dt)) % 360.0


    def rotate_right(self, dt):
        """
        Rotates camera to right.
        dt -- delta time
        """
        self.alpha = (self.alpha - (self.CAMERA_SPEED * dt)) % 360.0


##############################################################################################################

class World:
    """
    Grid based world. Each wall is a cube whose sides've got a size of 
    cell_size units. Public attributes:
    * cell_size -- Grid's side size. It must be a power of two 
    (default 128 units)
    * WALL_COLOR -- Wall color (tuple of (R,G,B) from 0 to 255)
    * FLOOR_COLOR -- Floor color (tuple of (R,G,B) from 0 to 255)
    * map -- List of list that stores the grid maps.
    * nrows -- Map number of rows
    * ncols -- Map number of columns
    """

    def __init__(self, cell_size=128, wall_color=(160,82,45), floor_color=(34,34,34)):
        self.cell_size = cell_size
        self.WALL_COLOR = wall_color
        self.FLOOR_COLOR = floor_color


    def get_cell_size(self):
        "Cell size getter"
        return self._cell_size


    def set_cell_size(self, new_value):
        "Cell size setter"
        if new_value == 0 or (new_value & (new_value-1)) != 0:
            raise ValueError("[ERROR] World.cell_size must be a power of two")
        else:
            self._cell_size = new_value


    def load_map(self, path):
        """
        Creates a map from .map file. In this map file, "W" represents walls,
        and "-" represents an empty cell, separed by space. See example.map.
        path -- path to map file
        Restrictions: The number of colums must be the same on each row. Map
        can only have "W" or "-" characters, spared by space.
        """
        
        try:
            file = open(path, 'r')
            rows = [line.strip().split(" ") for line in file]
            file.close()
    
            # Check that file wasn't empty
            if len(rows) <= 0:
                raise ValueError

            # Number of colums must be the same
            n_cols = len(rows[0])
            for row in rows:
                if len(row) != n_cols:
                    raise ValueError

            # Map must contains only "W" or "-"
            flat_list = list(itertools.chain.from_iterable(rows))
            for element in flat_list:
                if element not in "W-":
                    raise ValueError

            self.map = rows
            self.nrows = len(self.map)
            self.ncols = len(self.map[0])
            
        except IOError:
            print("[ERROR] In World.load_map():", path, "could not be found")
            sys.exit(-1)
        except ValueError:
            print("[ERROR] In World.load_map():", path, "doesn't contains a map definition")
            sys.exit(-1)

    # Set cell_size as property:
    cell_size = property(get_cell_size, set_cell_size)

##############################################################################################################

class RenderEngine:
    """
    This class show the "fake" 3D render from a 2D map using RayCasting. 
    Public attributes:
    * player -- A player definition (object of type Player)
    * world -- A world definition, with a map loaded (object of type World)
    * pp_width -- Projection plane width (default 640 units)
    * pp_height -- Projection plane height (default 600 units)
    * FPS -- Engine frames per second (default 40)
    Note: Projection plane is equivalent to viewport.
    """

    def __init__(self, player, world, pp_width=640, pp_height=400, FPS=40):
        self.player = player
        self.world = world
        self.pp_width = pp_width
        self.pp_height = pp_height
        self.FPS = FPS

        # Compute another proyection attributes:
        # Distance between player and proyection plane:
        self.__distance_to_pp = (pp_width>>1) / math.tan(math.radians(player.FOV>>1))
        # Angle between subsequent raycast:
        self.__angle_btw_rc = player.FOV / pp_width
        # Projection Plane center:
        self.__PP_CENTER = pp_height>>1
        # Get cell size coef, for speed up divisions:
        self.__CS_COEF = int(math.log2(world.cell_size))
        # This constant is used for project wall slices:
        self.__PROJ_CONST = self.world.cell_size * self.__distance_to_pp

    
    def toCell(self, world_coordinate):
        "Convert from world coordinates to cell coordinates."
        return int(world_coordinate) >> self.__CS_COEF
    

    @staticmethod
    def toWorld(cell_coordinate, cell_size=128):
        """
        Returns the world coordinates associated with center's cell
        cell_coordinate -- Integer coordinate of cell
        cell_size -- World's cells size (default 128)
        """
        return float((cell_coordinate * cell_size) + (cell_size>>1))

        
    def __check_collisions(self):
        "Prevents the player from going through the walls"

        X = self.toCell(self.player.x)
        Y = self.toCell(self.player.y)
        
        if self.world.map[Y][X] == "W":
            self.player.x = self._last_non_colliding_pos[0]
            self.player.y = self._last_non_colliding_pos[1]
            return True
        
        return False

    
    def init(self, title="RayCast Render Engine"):
        """
        Init pyglet and creates the window.
        Return a reference to window.
        """

        self._last_player_pos = None
        self._last_non_colliding_pos = (self.player.x, self.player.y)
        self.window = pyglet.window.Window(width=self.pp_width, height=self.pp_height, caption=title)
        
        return self.window


    def render_scene(self):
        "Draw the scene using pyglet."

        # Functions used to compute color (using distance)
        clamp = lambda v, up: int(max(0, min(v, self.world.WALL_COLOR[up])))
        dotcolor = lambda c, f: (clamp(c[0]*f, 0), clamp(c[1]*f, 1), clamp(c[2]*f, 2))
        intensity = lambda d: 1/d * 200 * (self.world.cell_size >> self.__CS_COEF)

        # Only redraw if player has moved:
        if self._last_player_pos != (self.player.x, self.player.y, self.player.alpha):
            # Clear screen:
            self.window.clear()

            # Check collision:
            if not self.__check_collisions():
                self._last_non_colliding_pos = (self.player.x, self.player.y)

            # Draw floor
            rect = (
                0, 0,
                self.pp_width, 0,
                self.pp_width, self.__PP_CENTER,
                0, self.__PP_CENTER
            )

            pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
                ('v2i', rect),
                ('c3B', self.world.FLOOR_COLOR * 4)
            )

            # Draw walls
            slices = RayCast.cast_rays(self.player.x, self.player.y, self.player.alpha, \
                self.world.ncols, self.world.nrows, self.world.cell_size, self.world.map, \
                self.player.FOV, self.__PROJ_CONST, self.pp_width, self.__angle_btw_rc)
            
            for sl in slices:
                begin = self.__PP_CENTER - (sl[0] >> 1)
                end = self.__PP_CENTER + (sl[0] >> 1)
                point = (sl[1], begin, sl[1], end)
                color = dotcolor(self.world.WALL_COLOR, intensity(sl[2])) * 2
                pyglet.graphics.draw(2, pyglet.gl.GL_LINES,
                    ('v2i', point),
                    ('c3B', color)
                )
        
        # Store last player pos:
        self._last_player_pos = (self.player.x, self.player.y, self.player.alpha)


    def run(self, main_loop):
        "Set pyglet main loop and start RenderEngine"

        if not inspect.isfunction(main_loop):
            print("[ERROR] In RenderEngine.run(): main_loop object must be a function")
            sys.exit(-1)
        elif len(inspect.getargspec(main_loop)[0]) != 1:
            print("[ERROR] In RenderEngine.run(): main_loop object must only have one argument called 'dt'")
            sys.exit(-1)
        elif inspect.getargspec(main_loop)[0][0] != 'dt':
            print("[ERROR] In RenderEngine.run(): main_loop object must only have one argument called 'dt'")
            sys.exit(-1)
    
        pyglet.clock.schedule_interval(main_loop, 1/self.FPS)
        pyglet.app.run()