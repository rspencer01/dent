import os
import sys

if getattr(sys, "frozen", False):
    os.chdir(sys._MEIPASS)

import time
import logging
import numpy as np
import numpy.linalg
from . import taskQueue
import OpenGL.GL as gl
import OpenGL.GLU as glu
import OpenGL.GLUT as glut
from PIL import Image
import random

from . import args

args.parse()

LOGGING_FORMAT = "%(asctime)-15s <%(threadName)-12s> [%(module)-12s] - %(message)s"
if args.args.verbose >= 2:
    logging.basicConfig(format=LOGGING_FORMAT, level=logging.DEBUG)
elif args.args.verbose == 1:
    logging.basicConfig(format=LOGGING_FORMAT, level=logging.INFO)
else:
    logging.basicConfig(format=LOGGING_FORMAT, level=logging.WARN)

logging.getLogger("pyassimp").setLevel(logging.INFO)

from . import messaging
from . import configuration
import dent.graphics
import dent.inputs
import dent.debug

from . import assets
assets.initialise()

windowHeight = 512
windowWidth = 512
frametime = 0.
lastframe = time.time()
trianglesQuery = None
frametimes = [0 for _ in range(200)]
frametimecount = 0


def display():
    glut.glutSwapBuffers()
    global frametime, lastframe, trianglesQuery, frametimes, frametimecount
    thisframetime = time.time() - lastframe
    frametimes[frametimecount % len(frametimes)] = thisframetime
    frametimecount += 1
    frametime = frametime * .8 + 0.2 * thisframetime
    lastframe = time.time()

    messaging.process_messages()

    if not trianglesQuery:
        trianglesQuery = gl.glGenQueries(1)
    gl.glBeginQuery(gl.GL_PRIMITIVES_GENERATED, trianglesQuery)

    scene.render(windowWidth, windowHeight)

    gl.glEndQuery(gl.GL_PRIMITIVES_GENERATED)
    triangleCount = gl.glGetQueryObjectiv(trianglesQuery, gl.GL_QUERY_RESULT)

    glut.glutSetWindowTitle(
        "Dent {:.2f} ({:.0f}ms) {:.6f} {:,} triangles".format(
            1. / frametime, frametime * 1000, time.time() - lastframe, triangleCount
        )
    )
    glut.glutPostRedisplay()


def takeScreenshot():
    viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
    pixels = gl.glReadPixels(
        viewport[0],
        viewport[1],
        viewport[2],
        viewport[3],
        gl.GL_RGB,
        gl.GL_UNSIGNED_BYTE,
    )

    image = Image.frombytes(
        "RGB", (viewport[2] - viewport[0], viewport[3] - viewport[0]), pixels
    )
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    image.save("screenshot.png")


def glut_timer_handler(fps):
    messaging.add_message(messaging.Message("timer", (fps,)))


def timer_handler(fps):
    taskQueue.doNextTask()

    glut.glutTimerFunc(1000 // fps, glut_timer_handler, fps)




def reshape_handler(width, height):
    global windowHeight, windowWidth
    windowHeight = height
    windowWidth = width
    for scene in scenes:
        for stage in scene.renderPipeline.stages:
            stage.reshape(width, height)


def keyboard_handler(key):
    global scene
    if key == "\033":
        if args.args.replay is None:
            messaging.save_messages()
        if trianglesQuery:
            gl.glDeleteQueries(1, [trianglesQuery])
        logging.info(
            "Average frame time {:.4f} (+-{:.4f})".format(
                sum(frametimes) / len(frametimes), np.std(frametimes)
            )
        )
        logging.warn("Exiting...")
        sys.exit(0)
    if key == "~":
        if args.args.replay is None:
            userCommand()
    if key == "t":
        messaging.add_message(messaging.Message("screenshot", ()))
    if key == "u":
        for i in scenes:
            if i != scene:
                scene = i
                break

    if key == "r":
        if dent.inputs.hold_mouse:
            glut.glutSetCursor(glut.GLUT_CURSOR_INHERIT)
        else:
            glut.glutSetCursor(glut.GLUT_CURSOR_NONE)
        dent.inputs.hold_mouse = not dent.inputs.hold_mouse
    if key == "?":
        print((open("help").read()))


def mouse_handler(button, state, x, y):
    if button in (3, 4):
        scene.camera.lockDistance += button - 3.5


def game_start_handler(time):
    logging.info("Game start!")
    glut.glutTimerFunc(1000 // 60, glut_timer_handler, 60)


def userCommand():
    command = input(">>> ")
    while (command not in ["continue", "exit"]):
        try:
            exec(command, globals())
        except Exception as e:
            print(("Exception:", e))
        command = input(">>> ")


dent.graphics.initialise_graphics()
dent.inputs.initialise_inputs()
dent.debug.initialise_debug()
glut.glutDisplayFunc(display)

from . import Texture

Texture.initialise()

import scenes as game_scenes

scenes = [scene() for scene in game_scenes.__scenes__]
scene = [i for i in scenes if type(i) == game_scenes.__starting_scene__][0]

messaging.add_handler("mouse", mouse_handler)
messaging.add_handler("keyboard", keyboard_handler)
messaging.add_handler("timer", timer_handler)
messaging.add_handler("game_start", game_start_handler)
messaging.add_handler("screenshot", takeScreenshot)
messaging.add_handler("window_reshape", reshape_handler)

logging.info("Initialisation finished")
messaging.add_message(messaging.Message("game_start", (time.time(),)))
if args.args.replay:
    messaging.load_replay(args.args.replay)
glut.glutMainLoop()
