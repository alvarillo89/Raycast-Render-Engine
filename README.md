# Raycast Render Engine
A Ray-casting 2D render engine based on python3 and pyglet. Inspired in retro FPS games.

### Usage:
1. Download `requirements.txt`, `RayCastRenderEngine.py` and `RayCast.pyx`.
2. You need to have Python3 installed, then run:

```bash
pip install -r requirements.txt
```

In `example.map` and `ExampleGame.py` files, you can see an example of how to create custom maps and the use of the library respectively.

A custom map is just a plain text file with .map extension. "W" represents a wall and "-" represents a blank space. **Maps are represented internally as a matrix of cells. Make sure that all rows and columns have the same dimensions, filling with "-" if necessary.**

For running a game just type:

```bash
python3 ExampleGame.py
```
