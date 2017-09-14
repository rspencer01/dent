import logging
import OpenGL.GL as gl
from ShaderFile import ShaderFile

universalUniforms = {}

from GenericShader import GenericShader
from InstancedShader import InstancedShader
from TesselationShader import TesselationShader
from TransformFeedbackShader import TransformFeedbackShader

shaders = {}

def setUniversalUniforms(shader):
  for key, value in universalUniforms.items():
    shader[key] = value

def updateUniversalUniform(key, value):
  for name, shader in shaders.items():
    shader[key] = value
  universalUniforms[key] = value

def getShader(name, tess=False, instance=False, geom=False):
  global shaders
  if name not in shaders:
    logging.info("Loading shader '{:s}'".format(name))
    if not tess:
      if not instance:
        shaders[name] = GenericShader(
                               name,
                               ShaderFile('shaders/'+name+'/fragment.shd', gl.GL_FRAGMENT_SHADER),
                               ShaderFile('shaders/'+name+'/vertex.shd', gl.GL_VERTEX_SHADER),
                               geom and ShaderFile('shaders/'+name+'/geometry.shd', gl.GL_GEOMETRY_SHADER)
                               )
      else:
        shaders[name] = InstancedShader(
                               name,
                               ShaderFile('shaders/'+name+'/fragment.shd', gl.GL_FRAGMENT_SHADER),
                               ShaderFile('shaders/'+name+'/vertex.shd', gl.GL_VERTEX_SHADER),
                               geom and ShaderFile('shaders/'+name+'/geometry.shd', gl.GL_GEOMETRY_SHADER)
                               )
    else:
      shaders[name] = TesselationShader(
                               name,
                               ShaderFile('shaders/'+name+'/fragment.shd', gl.GL_FRAGMENT_SHADER),
                               ShaderFile('shaders/'+name+'/vertex.shd', gl.GL_VERTEX_SHADER),
                               geom and ShaderFile('shaders/'+name+'/geometry.shd', gl.GL_GEOMETRY_SHADER),
                               ShaderFile('shaders/'+name+'/tesscontrol.shd', gl.GL_TESS_CONTROL_SHADER),
                               ShaderFile('shaders/'+name+'/tesseval.shd', gl.GL_TESS_EVALUATION_SHADER)
                               )
    setUniversalUniforms(shaders[name])
  return shaders[name]

def setUniform(name,value):
  for i in shaders:
    shaders[i][name] = value

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser(description='Magrathea shader source inspector.')
  parser.add_argument('file',
      help='source file')
  args = parser.parse_args()

  print ShaderFile(args.file, None).getSource()
