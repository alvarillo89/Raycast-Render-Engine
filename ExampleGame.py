# -*- coding: utf-8 -*-

"""
##############################################################################################################
@author Álvaro Fernández García
@version 1.4
@date 4, feb, 2019

A Ray-casting 2D render engine based on python3 and pyglet.
Inspired in retro FPS games.

Here is an example of its use.
##############################################################################################################
"""

import pyglet
from pyglet.window import key
from RayCastRenderEngine import RenderEngine, World, Player


# Create a player object (you can use toWorld function to set its initial position)
player = Player(x=RenderEngine.toWorld(3), y=RenderEngine.toWorld(2), alpha=270)

# Create a world object and load a map to it:
world = World()
world.load_map("example.map")

# Create the render engine with player and world objects:
engine = RenderEngine(player, world)

# Init engine:
window = engine.init()

# Tell to Pyglet that it must update view calling engine.render_scene() function: 
@window.event
def on_draw():
    engine.render_scene()

# Define Input events and main loop game (dt is deltaTime):
keys = key.KeyStateHandler()
window.push_handlers(keys)
def main_loop(dt):
    if keys[key.W]:
        engine.player.move_forward(dt)
    if keys[key.A]:
        engine.player.rotate_left(dt)
    if keys[key.S]:
        engine.player.move_backward(dt)
    if keys[key.D]:
        engine.player.rotate_right(dt)

# Run engine: (should call this and not pyglet.run()!)
engine.run(main_loop)