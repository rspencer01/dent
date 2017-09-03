Dent
====

Dent is a work-in-progress 3D game engine.  The idea is to get most of the boring stuff out of the way so that you can develop your game quickly, but still allow access to lower level objects, so that if you need to do any finicky graphics thing you can.

Should I Use Dent?
------------------
If you want to hack together a game in Python, don't want to fiddle around with OpenGL much and  are not too concerned about high levels of polish, I'd say "yes".

Dent offers smoothing over some of the bumps of getting up and running with OpenGL and python game development.  Some of the features offered are:

 * Shaders: 
   * Loading and compiling GLSL from disk
   * `#include` one file inside another
   * Smart uniform loading
   * Vertex attribute handling
   * Transform feedback shaders
   * Tesselation shaders
 * Texture abstraction with loading/saving from image files
 * Asset manager
 * 3D asset objects to populate your scenes
 * Built in game replay mechanism
 * Configuration files (for levels of graphics etc) handling
 * Render pipelines to do advanced lighting/differed shading

However.

Dent is in no way complete.  It is very much a work in progress, with bits being added here and there.  At the moment, because it has very little use, there are quite a few areas that need some improvement.  I'd be very happy to have some pull requests.


How Do I Get Dent?
------------------
At the moment it is suggested to clone the Dent repository into a folder called `dent` inside your project (see below).  In the future this may change to a `pip install` or a `python setup.py` installation.

Minimal Directory Layout
------------------------

For a pretty minimal game, check out [pong](https://github.com/rspencer01/pong).  In overview, a typical game would have the following directory structure:

~~~
├── dent
│   ├── args.py
│   ├── ...
│   └── transforms.py
├── my-awesome-game.py
├── scenes
│   ├── __init__.py
│   └── MainScene.py
└── shaders
    ├── image
    │   ├── fragment.shd
    │   └── vertex.shd
    └── ...
~~~

The file `my-awesome-game.py` is the entry point to the game (you would run the game as `python my-awesome-game.py`).  It is moderately minimal, and could simply look like this

~~~ python
#!/usr/bin/env python

import dent.core
~~~

The file `scenes/__init__.py` is similarly minimal:

``` python
from MainScene import MainScene

__scenes__ = set([MainScene])
__starting_scene__ = MainScene
```

The items in `shaders/` are the GLSL shaders you will use to render your game.  Take a look at the pong project above for a very simple one.

All of the logic will reside in `MainScene.py`.  For example:

``` python
import dent.Scene as Scene
import dent.RectangleObjects as RectangleObjects
from dent.RenderStage import RenderStage
import dent.messaging as messaging

class MainScene(Scene.Scene):
  def __init__(self):
    super(MainScene, self).__init__()
    self.renderPipeline.stages.append(
        RenderStage(render_func=self.display, final_stage=True)
        )

    import dent.Texture
    dent.Texture.getWhiteTexture().load()

    self.ball = RectangleObjects.BlankImageObject()
    self.ball.width = self.ball.height = 0.01

    messaging.add_handler('timer', self.timer)
    messaging.add_handler('keyboard', self.key_down)
    messaging.add_handler('keyboard_up', self.key_up)

  def display(self, **kwargs):
    self.ball.display()

  def key_down(self, key):
    # Do key down things

  def key_up(self, key):
    # Do key up things

  def timer(self, fps):
  	# Do timer things
```

Where Are The Docs?
-------------------
Working on it...