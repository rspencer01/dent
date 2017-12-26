import re
import os
import pkg_resources
import OpenGL.GL as gl

INCLUDE = -1

class ShaderCompileException(Exception):
  def __init__(self, args):
    message, source = args
    errp = re.compile(r"0\((.+?)\)(.*)")
    m = errp.match(message)
    if not m or not source:
      Exception.__init__(self, message)
      return
    line = int(m.groups()[0])
    ret = '\n\n'+message+'\n'
    sourceLines = source.split('\n')
    for i in xrange(max(0,line-4),min(len(sourceLines)-1,line+5)):
      ret += ('>>|' if i == line-1 else '  |') + sourceLines[i]+'\n'
    Exception.__init__(self, ret)


class ShaderFile(object):
  def __init__(self, name, type):
    self.name = name
    self.type = type
    self.load_from_source()


  def get_source(self):
    if self.type == INCLUDE:
      if os.path.isfile('shaders/{}'.format(self.name)):
        return open('shaders/{}'.format(self.name)).read()
      if pkg_resources.resource_exists(__name__, 'default_shaders/includes/{}'.format(self.name)):
        return pkg_resources.resource_string(__name__, 'default_shaders/includes/{}'.format(self.name))
      raise IOError("Shader '{}' not found".format(self.name))
    suffix = {
        gl.GL_FRAGMENT_SHADER: 'fragment.shd',
        gl.GL_GEOMETRY_SHADER: 'geometry.shd',
        gl.GL_TESS_CONTROL_SHADER: 'tesscontrol.shd',
        gl.GL_TESS_EVALUATION_SHADER: 'tesseval.shd',
        gl.GL_VERTEX_SHADER: 'vertex.shd',
        }[self.type]
    if os.path.isfile(self.name) and self.name[:-4] == '.shd':
      return open(self.name).read()
    if os.path.isfile('shaders/{}/{}'.format(self.name, suffix)):
      return open('shaders/{}/{}'.format(self.name, suffix)).read()
    if pkg_resources.resource_exists(__name__, 'default_shaders/{}/{}'.format(self.name, suffix)):
      return pkg_resources.resource_string(__name__, 'default_shaders/{}/{}'.format(self.name, suffix))
    raise IOError("Shader '{}' not found".format(self.name))


  def load_from_source(self):
    source = self.get_source()
    p = re.compile(r"#include\W(.+);")
    m = p.search(source)
    while m:
      included = ShaderFile(m.group(1), INCLUDE)
      source = source.replace("#include {};".format(m.group(1)), included.getSource())
      m = p.search(source)
    self.uniforms = []
    self.headers = []
    self.code = []
    headers = True
    for i in source.split('\n'):
      if 'uniform' in i:
        self.uniforms.append(' '.join(i.split()))
        headers = False
      elif headers:
        self.headers.append(i)
      else:
        self.code.append(i)

    self.uniforms = list(set(self.uniforms))
    self.program = None


  def getSource(self):
    return  '\n'.join(
        self.headers + self.uniforms + self.code)


  def getProgram(self):
    if self.program is None:
      self.program = gl.glCreateShader(self.type)
      gl.glShaderSource(self.program, self.getSource())
      gl.glCompileShader(self.program)
      # Find compile errors
      if gl.glGetShaderiv(self.program, gl.GL_COMPILE_STATUS) != gl.GL_TRUE:
          raise ShaderCompileException((gl.glGetShaderInfoLog(self.program), self.getSource()))
    return self.program
