import numpy as np
import pyassimp
import Camera
import Texture
import Image
import os
import Shaders
import transforms
import OpenGL.GL as gl

shader          = Shaders.getShader('general',instance=True)
shader['colormap'] = Texture.COLORMAP_NUM
billboardShader = Shaders.getShader('billboard',instance=True,geom=True)
billboardShader['colormap'] = Texture.COLORMAP_NUM
billboardShader['bumpmap'] = Texture.BUMPMAP_NUM
makeBillboardShader = Shaders.getShader('makeBillboard',instance=True)

class MultiObject(object):
  def __init__(
      self,
      filename,
      name=None,
      scale=1):

    if name == None:
      name = os.path.basename(filename)

    self.name = name
    self.meshes = []
    self.renderIDs = []
    self.textures = []
    self.billboardMesh = None
    self.billboardRenderID = None
    self.billboardTexture = None
    self.instances = np.zeros(0, dtype=[('model', np.float32, (4, 4))])
    self.numInstances = None
    self.frozen = False
    self.scale = scale

    self.loadFromScene(filename, self.scale)

  def loadFromScene(self, scenePath, scale):
    scene = pyassimp.load(scenePath)
    self.directory = os.path.dirname(scenePath)
    self.boundingBox = [[1e3,1e3,1e3], [-1e3,-1e3,-1e3]]
    def addNode(node,trans):
      newtrans = trans.dot(node.transformation)
      for msh in node.meshes:
        self.addMesh(msh,newtrans)
      for nod in node.children:
        addNode(nod,newtrans)
    addNode(scene.rootnode,np.eye(4))
    self.makeBillboard()
    self.makeBillboardMesh()

  def addMesh(self,mesh,trans):
    data = np.zeros(len(mesh.vertices),
                      dtype=[("position"  , np.float32, 3),
                             ("normal"    , np.float32, 3),
                             ("textcoord" , np.float32, 2),
                             ("color"     , np.float32, 4)])
    # Get the vertex positions and add a w=1 component
    vertPos = mesh.vertices
    add = np.zeros((vertPos.shape[0], 1), dtype=np.float32)+1
    vertPos = np.append(vertPos,add,axis=1)
    # Get the vertex normals and add a w=1 component
    vertNorm = mesh.normals
    add = np.zeros((vertNorm.shape[0], 1), dtype=np.float32)
    vertNorm = np.append(vertNorm, add, axis=1)
    # Transform all the vertex positions.
    for i in xrange(len(vertPos)):
      vertPos[i] = trans.dot(vertPos[i])
      vertNorm[i] = trans.dot(vertNorm[i])
    # Splice correctly
    vertPos = vertPos[:, 0:3]
    vertNorm = vertNorm[:, 0:3]

    # Set the data
    data["position"] = vertPos*self.scale
    data["normal"] = vertNorm
    data["textcoord"] = mesh.texturecoords[0][:, [0,1]]
    data["color"] = 1

    # Update bounding box
    self.boundingBox[0] = np.min([self.boundingBox[0],
                                  np.min(data["position"], 0)], 0)
    self.boundingBox[1] = np.max([self.boundingBox[1],
                                  np.max(data["position"], 0)], 0)

    # Get the indices
    indices = mesh.faces

    # Load the texture
    texture = Texture.Texture(Texture.COLORMAP)
    if 'file' in dict(mesh.material.properties.items()):
      teximag = Image.open(self.directory+'/'+dict(mesh.material.properties.items())['file'])
      texdata = np.array(teximag.getdata()).astype(np.float32)
      # Make this a 4 color file
      if (texdata.shape[1]!=4):
        add = np.zeros((texdata.shape[0], 1),dtype=np.float32)+256
        texdata = np.append(texdata,add,axis=1)
      texdata = texdata.reshape(teximag.size[0], teximag.size[1], 4)
      texture.loadData(texdata/256)

    #Add the textures and the mesh data
    self.textures.append(texture)
    self.meshes.append((data,indices,texture))

  def freeze(self, instanceBuffer=None):
    """If instanceBuffer is specified, uses that buffer for the instance data
    instead of the give instance information."""
    for data,indices,texture in self.meshes:
      self.renderIDs.append(shader.setData(data,indices,self.instances))
    self.billboardRenderID = billboardShader.setData(self.billboardMesh[0], self.billboardMesh[1],self.instances, instanceBuffer)
    self.frozen = True

  def render(self,offset,num=None):
    shader.load()
    if num==None: num = len(self.instances)
    for mesh,renderID in zip(self.meshes,self.renderIDs):
      # Load texture
      mesh[2].load()
      shader.draw(gl.GL_TRIANGLES,renderID,num,offset)


  def renderBillboards(self, offset, count=None):
    """Renders a particular number of billboards, starting from a certain
    offset.  If no count is specified, the maximum possible are rendered."""
    if count is None:
      if self.numInstances is None:
        count = len(self.instances) - offset
      else:
        count = self.numInstances
    # Load texture
    self.billboardTexture.load()
    self.billboardnormalTexture.load()
    # Do the render
    billboardShader.draw(gl.GL_TRIANGLES, self.billboardRenderID, count, offset)


  def makeBillboard(self):
    numberOfSwatches = 5
    texSize = 512

    instance = np.zeros(numberOfSwatches, dtype=[('model', np.float32, (4, 4))])
    width = 2*max([(self.boundingBox[0][0]**2 + self.boundingBox[1][2]**2)**0.5,
                   (self.boundingBox[1][0]**2 + self.boundingBox[0][2]**2)**0.5,
                   (self.boundingBox[1][0]**2 + self.boundingBox[1][2]**2)**0.5,
                   (self.boundingBox[0][0]**2 + self.boundingBox[0][2]**2)**0.5])
    for i in xrange(numberOfSwatches):
      instance[i] = np.eye(4, dtype=np.float32)
      transforms.yrotate(instance['model'][i], i*360.0/numberOfSwatches)
      transforms.translate(instance['model'][i], i * width, 0, 0)
    renderIDs = []

    for data, indices, texture in self.meshes:
      renderIDs.append(makeBillboardShader.setData(data, indices, instance))

    # TODO This is a renderstage
    framebuffer = gl.glGenFramebuffers(1)
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, framebuffer)

    self.billboardTexture = Texture.Texture(Texture.COLORMAP)
    self.billboardTexture.loadData(np.ones((texSize*numberOfSwatches,texSize, 4),dtype=np.float32))
    self.billboardnormalTexture = Texture.Texture(Texture.BUMPMAP)
    self.billboardnormalTexture.loadData(np.ones((texSize*numberOfSwatches,texSize, 4),dtype=np.float32))

    depthbuffer = gl.glGenRenderbuffers(1)
    gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, depthbuffer)
    gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT, texSize*numberOfSwatches, texSize)
    gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_RENDERBUFFER, depthbuffer)

    gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, self.billboardTexture.id, 0);
    gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT1, self.billboardnormalTexture.id, 0);

    gl.glDrawBuffers(2,[gl.GL_COLOR_ATTACHMENT0, gl.GL_COLOR_ATTACHMENT1])
    gl.glViewport(0,0,texSize*numberOfSwatches, texSize)

    camera = Camera.Camera(np.array([0,0,40]))
    camera.render()
    camera.render('user')

    gl.glClear(gl.GL_DEPTH_BUFFER_BIT| gl.GL_COLOR_BUFFER_BIT)
    projection = transforms.ortho(-width/2, width/2 + (numberOfSwatches-1)*width, self.boundingBox[0][1], self.boundingBox[1][1], 0.1, 100)
    Shaders.setUniform('projection', projection)

    for mesh,renderID in zip(self.meshes,renderIDs):
      mesh[2].load()
      makeBillboardShader['colormap'] = Texture.COLORMAP_NUM
      makeBillboardShader.draw(gl.GL_TRIANGLES,renderID,len(instance),0)

    self.billboardTexture.makeMipmap()
    self.billboardnormalTexture.makeMipmap()

    gl.glDeleteRenderbuffers(1, [depthbuffer])
    gl.glDeleteFramebuffers(1, [framebuffer])


  def makeBillboardMesh(self):
    """Constructs the mesh data for the billboard."""
    width = 2*max([(self.boundingBox[0][0]**2 + self.boundingBox[1][2]**2)**0.5,
                   (self.boundingBox[1][0]**2 + self.boundingBox[0][2]**2)**0.5,
                   (self.boundingBox[1][0]**2 + self.boundingBox[1][2]**2)**0.5,
                   (self.boundingBox[0][0]**2 + self.boundingBox[0][2]**2)**0.5])
    data = np.zeros(4, dtype=[("position"  , np.float32, 3),
                              ("normal"    , np.float32, 3),
                              ("textcoord" , np.float32, 2),
                              ("color"     , np.float32, 4)])
    data["position"] = [(-width/2, self.boundingBox[0][1], 0),
                        (-width/2, self.boundingBox[1][1], 0),
                        ( width/2, self.boundingBox[1][1], 0),
                        ( width/2, self.boundingBox[0][1], 0)]
    data["normal"] = 1
    data["textcoord"] = [[0, 0], [0, 1], [1, 1], [1, 0]]
    data["color"] = 1
    indices = np.array([[1, 0, 2], [2, 0, 3]], dtype=np.int32)
    self.billboardMesh = (data,indices)


  def display(self, pos, shadows=False):
    if not self.frozen:
      return
    # Render the billboards
    self.renderBillboards(0)
