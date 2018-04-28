import OpenGL.GLUT as glut
import logging
import dent.messaging
import dent.args

hold_mouse = True
windowHeight = 512
windowWidth = 512

def glut_keyboard_handler(key, *args):
    dent.messaging.add_message(dent.messaging.Message("keyboard", (key)))


def glut_keyboard_up_handler(key, *args):
    dent.messaging.add_message(dent.messaging.Message("keyboard_up", (key)))


def glut_mouse_handler(button, state, x, y):
    dent.messaging.add_message(dent.messaging.Message("mouse", (button, state, x, y)))


def glut_mouse_motion_handler(x, y):
    dent.messaging.add_message(dent.messaging.Message("mouse_motion", (x, y)))

def hold_mouse_motion_handler(x, y):
    if (x != windowWidth / 2 or y != windowHeight / 2) and hold_mouse:
        glut.glutWarpPointer(windowWidth / 2, windowHeight / 2)

def reshape_handler(width, height):
    global windowHeight, windowWidth
    windowHeight = height
    windowWidth = width

def initialise_inputs():
    logging.debug("Initialising GLUT Mouse and Keyboard inputs")
    if dent.args.args.replay is None:
        glut.glutMouseFunc(glut_mouse_handler)
        glut.glutPassiveMotionFunc(glut_mouse_motion_handler)
        glut.glutMotionFunc(glut_mouse_motion_handler)
        glut.glutKeyboardFunc(glut_keyboard_handler)
        glut.glutKeyboardUpFunc(glut_keyboard_up_handler)

    dent.messaging.add_handler("mouse_motion", hold_mouse_motion_handler)
    dent.messaging.add_handler("window_reshape", reshape_handler)
