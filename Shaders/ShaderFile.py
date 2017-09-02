import re
import OpenGL.GL as gl

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
  def __init__(self, filename, type):
    source = open(filename).read()
    p = re.compile(r"#include\W(.+);")
    m = p.search(source)
    while m:
      included = ShaderFile(m.group(1), type)
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
    self.type = type


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
