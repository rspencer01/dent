import os
import sys
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)

import time
import logging
import numpy as np
import numpy.linalg
import taskQueue
import OpenGL.GL as gl
import OpenGL.GLU as glu
import OpenGL.GLUT as glut
import Image
import messaging
import random

import args
args.parse()

LOGGING_FORMAT = '%(asctime)-15s <%(threadName)-12s> [%(module)-12s] - %(message)s'
if args.args.verbose:
  logging.basicConfig(format=LOGGING_FORMAT, level=logging.DEBUG)
else:
  logging.basicConfig(format=LOGGING_FORMAT, level=logging.INFO)

import configuration

Re = 6.360e6

program = None
windowHeight = 512
windowWidth = 512
cameraSpeed = 20
frametime = 0.
lastframe = time.time()
hold_mouse = True
fastMode = False
trianglesQuery = None
frametimes = [0 for _ in xrange(200)]
frametimecount = 0

aboveGround = 1

def display():
  glut.glutSwapBuffers()
  global frametime,lastframe, trianglesQuery, frametimes, frametimecount
  thisframetime = time.time()-lastframe
  frametimes[frametimecount % len(frametimes)] = thisframetime
  frametimecount += 1
  frametime = frametime*.8 + 0.2*thisframetime
  lastframe = time.time()

  messaging.process_messages()

  if not trianglesQuery:
    trianglesQuery = gl.glGenQueries(1)
  gl.glBeginQuery(gl.GL_PRIMITIVES_GENERATED, trianglesQuery)

  scene.render(windowWidth, windowHeight)

  gl.glEndQuery(gl.GL_PRIMITIVES_GENERATED)
  triangleCount = gl.glGetQueryObjectiv(trianglesQuery, gl.GL_QUERY_RESULT)

  glut.glutSetWindowTitle("{:.2f} ({:.0f}ms) {:.6f} {:,} triangles".format(1./frametime,frametime*1000, time.time()-lastframe, triangleCount))
  glut.glutPostRedisplay()

def takeScreenshot():
  viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
  pixels = gl.glReadPixels(viewport[0], viewport[1], viewport[2], viewport[3], gl.GL_RGB, gl.GL_UNSIGNED_BYTE)

  image = Image.fromstring("RGB", (viewport[2]-viewport[0], viewport[3]-viewport[0]), pixels)
  image = image.transpose( Image.FLIP_TOP_BOTTOM)
  image.save("screenshot.png")

def glut_timer_handler(fps):
  messaging.add_message(messaging.Message('timer', (fps,)))

def timer_handler(fps):
  if 'w' in keys:
    scene.camera.move(scene.cameraSpeed * 1.0/fps)
    if scene.camera.lockObject:
      scene.Characters.setCharacterDirection(scene.camera.direction)
      scene.Characters.move(0.5)
  if 's' in keys:
    scene.camera.move(scene.cameraSpeed * -1.0/fps)
    if scene.camera.lockObject:
      scene.Characters.setCharacterDirection(scene.camera.direction)
      scene.Characters.move(-0.5)
  if 'e' in keys:
    scene.camera.rotUpDown(1.5/fps)
  if 'q' in keys:
    scene.camera.rotUpDown(-1.5/fps)
  if 'a' in keys:
    scene.camera.rotLeftRight(-1.5/fps)
  if 'd' in keys:
    scene.camera.rotLeftRight(1.5/fps)
  if 'h' in keys:
    scene.camera.position = scene.camera.position * 0.98

  taskQueue.doNextTask()

  glut.glutTimerFunc(1000/fps, glut_timer_handler, fps)

def mouse_motion_handler(x, y):
  if x != windowWidth/2 or \
     y != windowHeight/2:
    if hold_mouse:
      scene.camera.rotUpDown(0.01*(y-windowHeight/2.))
      scene.camera.rotLeftRight(0.01*(x-windowWidth/2.))
      glut.glutWarpPointer(windowWidth/2,windowHeight/2)

def reshape(width,height):
  global windowHeight,windowWidth
  windowHeight = height
  windowWidth = width
  for scene in scenes:
    for stage in scene.renderPipeline.stages:
      stage.reshape(width, height)

keys = set()
def keyboard_handler(key):
  global hold_mouse, fastMode, scene
  if key=='\033':
    if args.args.replay is None:
      messaging.save_messages()
    gl.glDeleteQueries(1, [trianglesQuery])
    logging.info("Average frame time {:.4f} (+-{:.4f})".format(sum(frametimes)/len(frametimes), np.std(frametimes)))
    logging.warn("Exiting...")
    sys.exit(0)
  if key=='~':
    if args.args.replay is None:
      userCommand()
  if key=='t':
    messaging.add_message(messaging.Message('screenshot',()))
  if key=='u':
    for i in scenes:
      if i != scene:
        scene = i
        break
  if key=='r':
    if hold_mouse:
      glut.glutSetCursor(glut.GLUT_CURSOR_INHERIT)
    else:
      glut.glutSetCursor(glut.GLUT_CURSOR_NONE)
    hold_mouse = not hold_mouse
  if key=='?':
    print open('help').read()
  keys.add(key)

def keyboard_up_handler(key):
  if key in keys:
    keys.remove(key)

def mouse_handler(button, state, x, y):
  if button in (3,4):
    scene.camera.lockDistance += button - 3.5
  if not hold_mouse:
    glut.glutWarpPointer(windowWidth/2,windowHeight/2)

def glut_keyboard_handler(key, x, y):
  messaging.add_message(messaging.Message('keyboard',(key)))

def glut_keyboard_up_handler(key, x, y):
  messaging.add_message(messaging.Message('keyboard_up',(key)))

def glut_mouse_handler(button, state, x, y):
  messaging.add_message(messaging.Message('mouse',(button, state, x, y)))

def glut_mouse_motion_handler(x, y):
  messaging.add_message(messaging.Message('mouse_motion',(x, y)))

def game_start_handler(time):
  logging.info("Game start!")
  glut.glutTimerFunc(1000/60, glut_timer_handler, 60)

def userCommand():
  command = raw_input('>>> ')
  while (command not in ['continue','exit']):
    try:
      exec(command,globals())
    except Exception as e:
      print "Exception:",e
    command = raw_input('>>> ')

glut.glutInit()
logging.info("Requesting OpenGL 4.2")
glut.glutInitContextVersion(4, 2);
glut.glutInitContextFlags(glut.GLUT_FORWARD_COMPATIBLE);
glut.glutInitContextProfile(glut.GLUT_CORE_PROFILE);
glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH)
glut.glutInitWindowSize(512,512);
glut.glutCreateWindow("PM4")
glut.glutSetKeyRepeat(glut.GLUT_KEY_REPEAT_OFF)
glut.glutIgnoreKeyRepeat(1)
logging.info("Obtained OpenGL "+gl.glGetString(gl.GL_VERSION))
logging.info("Uniform limit (vertex) {}".format(
  str(gl.glGetIntegerv(gl.GL_MAX_VERTEX_UNIFORM_COMPONENTS))))
gl.glEnable(gl.GL_DEPTH_TEST)
gl.glPolygonMode(gl.GL_FRONT_AND_BACK,gl.GL_FILL);
gl.glEnable(gl.GL_BLEND)
gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA);
gl.glCullFace(gl.GL_BACK)
glut.glutReshapeFunc(reshape)
glut.glutDisplayFunc(display)
if args.args.replay is None:
  glut.glutMouseFunc(glut_mouse_handler)
  glut.glutPassiveMotionFunc(glut_mouse_motion_handler)
  glut.glutKeyboardFunc(glut_keyboard_handler)
  glut.glutKeyboardUpFunc(glut_keyboard_up_handler)
glut.glutSetCursor(glut.GLUT_CURSOR_NONE)


import scenes as game_scenes

scenes = [scene() for scene in game_scenes.__scenes__]
scene = [i for i in scenes if type(i)==game_scenes.__starting_scene__][0]

messaging.add_handler('mouse', mouse_handler)
messaging.add_handler('mouse_motion', mouse_motion_handler)
messaging.add_handler('keyboard', keyboard_handler)
messaging.add_handler('keyboard_up', keyboard_up_handler)
messaging.add_handler('timer', timer_handler)
messaging.add_handler('game_start', game_start_handler)
messaging.add_handler('screenshot', takeScreenshot)

logging.info("Initialisation finished")
messaging.add_message(messaging.Message('game_start', (time.time(),)))
if args.args.replay:
  messaging.load_replay(args.args.replay)
glut.glutMainLoop()
