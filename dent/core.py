import os
import sys

if getattr(sys, "frozen", False):
    os.chdir(sys._MEIPASS)

import time
import logging
import numpy as np
import numpy.linalg
import taskQueue
import OpenGL.GL as gl
import OpenGL.GLU as glu
import OpenGL.GLUT as glut
from PIL import Image
import random

import args

args.parse()

LOGGING_FORMAT = "%(asctime)-15s <%(threadName)-12s> [%(module)-12s] - %(message)s"
if args.args.verbose >= 2:
    logging.basicConfig(format=LOGGING_FORMAT, level=logging.DEBUG)
elif args.args.verbose == 1:
    logging.basicConfig(format=LOGGING_FORMAT, level=logging.INFO)
else:
    logging.basicConfig(format=LOGGING_FORMAT, level=logging.WARN)

logging.getLogger("pyassimp").setLevel(logging.INFO)

import messaging
import configuration
import dent.graphics

windowHeight = 512
windowWidth = 512
frametime = 0.
lastframe = time.time()
hold_mouse = True
trianglesQuery = None
frametimes = [0 for _ in xrange(200)]
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

    glut.glutTimerFunc(1000 / fps, glut_timer_handler, fps)


def mouse_motion_handler(x, y):
    if x != windowWidth / 2 or y != windowHeight / 2 and hold_mouse:
        glut.glutWarpPointer(windowWidth / 2, windowHeight / 2)


def reshape_handler(width, height):
    global windowHeight, windowWidth
    windowHeight = height
    windowWidth = width
    for scene in scenes:
        for stage in scene.renderPipeline.stages:
            stage.reshape(width, height)


def keyboard_handler(key):
    global hold_mouse, scene
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
        if hold_mouse:
            glut.glutSetCursor(glut.GLUT_CURSOR_INHERIT)
        else:
            glut.glutSetCursor(glut.GLUT_CURSOR_NONE)
        hold_mouse = not hold_mouse
    if key == "?":
        print(open("help").read())


def mouse_handler(button, state, x, y):
    if button in (3, 4):
        scene.camera.lockDistance += button - 3.5


def glut_keyboard_handler(key, x, y):
    messaging.add_message(messaging.Message("keyboard", (key)))


def glut_keyboard_up_handler(key, x, y):
    messaging.add_message(messaging.Message("keyboard_up", (key)))


def glut_mouse_handler(button, state, x, y):
    messaging.add_message(messaging.Message("mouse", (button, state, x, y)))


def glut_mouse_motion_handler(x, y):
    messaging.add_message(messaging.Message("mouse_motion", (x, y)))


def game_start_handler(time):
    logging.info("Game start!")
    glut.glutTimerFunc(1000 / 60, glut_timer_handler, 60)


def userCommand():
    command = raw_input(">>> ")
    while (command not in ["continue", "exit"]):
        try:
            exec(command, globals())
        except Exception as e:
            print("Exception:", e)
        command = raw_input(">>> ")


dent.graphics.initialise_graphics()
glut.glutDisplayFunc(display)
if args.args.replay is None:
    glut.glutMouseFunc(glut_mouse_handler)
    glut.glutPassiveMotionFunc(glut_mouse_motion_handler)
    glut.glutMotionFunc(glut_mouse_motion_handler)
    glut.glutKeyboardFunc(glut_keyboard_handler)
    glut.glutKeyboardUpFunc(glut_keyboard_up_handler)

import Texture

Texture.initialise()

import scenes as game_scenes

scenes = [scene() for scene in game_scenes.__scenes__]
scene = [i for i in scenes if type(i) == game_scenes.__starting_scene__][0]

messaging.add_handler("mouse", mouse_handler)
messaging.add_handler("mouse_motion", mouse_motion_handler)
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
