import numpy as np
import transforms
from Shaders import *

class Camera:
  def __init__(
          self,
          position=np.array([0,0,0]),
          lockObject=None,
          lockDistance=50,
          move_hook=lambda x:x):
    """Initialises this camera at the given position.  If `lockObject` is not
    None, it must be a python object with a `position` attribute.  The camera
    will "follow" this object, as in a 3rd person game.

    The `move_hook` function will be called when the position of the camera
    changes with the new position.  It must return the actual position of the
    camera.  This is useful, for example to prevent the camera from moving
    within objects."""
    self.position = position
    self.lockObject = lockObject
    self.lockDistance = lockDistance

    self.move_hook = move_hook

    # Spherical coordinates are used to show the direction we
    # are looking in
    self.theta = 0
    self.phi = 0

    # There is a closest point we may get to the origin.  This
    # is a quick hack to prevent us going to the Earth
    self.minRadius = 0
    self.radiusCentre = np.array([0,0,0])
    # The "global" variables are the frame in which we rotate.
    # This allows, for example, for us to go around the earth
    # and still have "up" being away from the surface
    self.globalUp = np.array([0.0,1.0,0.0])
    self.globalRight = np.array([0.0,0.0,1.0])

    self.direction = np.array([0.,0.,1.])
    self.update()

  def move(self,d):
    self.update()
    if np.linalg.norm(self.position-self.radiusCentre-d*self.direction) >= self.minRadius:
      self.position += d * self.direction
      self.update()

  def rotUpDown(self,d):
    self.theta += d
    self.update()

  def rotLeftRight(self,d):
    self.phi += d
    self.update()

  def update(self):
    """Updates the internal representation of the camera, such as the view
    matrix and direction vector."""
    if self.lockObject is not None:
      self.position = self.lockObject.position + self.lockDistance * self.direction * np.array((-1,-1,-1))

    self.position = self.move_hook(self.position)

    self.view = np.eye(4,dtype=np.float32)
    view2 = np.eye(4,dtype=np.float32)
    transforms.translate(self.view,-self.position[0],-self.position[1],-self.position[2])
    view2[0:3,0] = np.cross(self.globalUp,self.globalRight)
    view2[0:3,1] = self.globalUp[:]
    view2[0:3,2] = self.globalRight[:]
    self.view = self.view.dot(view2)
    transforms.rotate(self.view,self.phi*180/3.1415,0,1,0)
    transforms.rotate(self.view,self.theta*180/3.1415,1,0,0)

    self.direction = np.array([0,0,-1])
    self.direction = self.view[:3,:3].dot(self.direction)



  def render(self, name=''):
    """Set the uniforms in all the shaders.  Uniform names are `{name}View`,
    `{name}CameraDirection` and `{name}CameraPosition` for a given name.  This
    allows for multiple cameras to be "rendered" simultaniously."""
    self.update()
    setUniform(name+'View',self.view.T)
    setUniform(name+'CameraDirection',self.direction)
    setUniform(name+'CameraPosition',self.position)
