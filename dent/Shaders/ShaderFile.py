import re
import os
import pkg_resources
import OpenGL.GL as gl

INCLUDE = -1

SHADER_FILENAMES = {
    gl.GL_FRAGMENT_SHADER: "fragment.shd",
    gl.GL_GEOMETRY_SHADER: "geometry.shd",
    gl.GL_TESS_CONTROL_SHADER: "tesscontrol.shd",
    gl.GL_TESS_EVALUATION_SHADER: "tesseval.shd",
    gl.GL_VERTEX_SHADER: "vertex.shd",
}

INCLUDE_MATCH_PATTERN = re.compile(r"#include\W(.+);")


class ShaderCompileException(Exception):

    def __init__(self, args):
        message, source = args
        errp = re.compile(r"0\((.+?)\)(.*)")
        m = errp.match(message)
        if not m or not source:
            Exception.__init__(self, message)
            return

        line = int(m.groups()[0])
        ret = "\n\n" + message + "\n"
        sourceLines = source.split("\n")
        for i in xrange(max(0, line - 4), min(len(sourceLines) - 1, line + 5)):
            ret += (">>|" if i == line - 1 else "  |") + sourceLines[i] + "\n"
        Exception.__init__(self, ret)


class ShaderFile(object):
    """A file-like object for accessing shader source code.

    This object locates shader source, exposes a `read` function, much like a file that
    returns the preprocessed code and preforms compilation to OpenGL programmes, ready
    for linking to a shader.

    Typical usage might be

      >>> shader_file = ShaderFile('beautiful-shader', gl.GL_FRAGMENT_SHADER)
      >>> shader_file.get_program()
      1
      >>> shader_file.read()
      "#version 4.0\n in vec3 position;\n..."
    """

    def __init__(self, name, shader_type):
        self.name = name
        self.shader_type = shader_type
        self.load_from_source()
        self.uniforms = []
        self.headers = []
        self.code = []
        self.program = None

    def get_source(self):
        """Searches for the unprocessed source code of this shader.

        Locations searched are the following in this order:
          * The name of the shader, as a single file, if its extension is `.shd`
          * Under the `shaders` directory if this is an include fragment
          * As a default dent include shader if this is an include fragment
          * Under the `shaders` directory, as a directory of files
          * As a default dent shader

        Failing to find this shader program in any of the above locations, this
        function will throw an `IOError`.
        """
        if os.path.isfile(self.name) and self.name[-4:] == ".shd":
            return open(self.name).read()

        if self.shader_type == INCLUDE:
            if os.path.isfile("shaders/{}".format(self.name)):
                return open("shaders/{}".format(self.name)).read()

            if pkg_resources.resource_exists(
                __name__, "default_shaders/includes/{}".format(self.name)
            ):
                return pkg_resources.resource_string(
                    __name__, "default_shaders/includes/{}".format(self.name)
                )

            raise IOError("Shader '{}' not found".format(self.name))

        suffix = SHADER_FILENAMES[self.shader_type]

        if os.path.isfile("shaders/{}/{}".format(self.name, suffix)):
            return open("shaders/{}/{}".format(self.name, suffix)).read()

        if pkg_resources.resource_exists(
            __name__, "default_shaders/{}/{}".format(self.name, suffix)
        ):
            return pkg_resources.resource_string(
                __name__, "default_shaders/{}/{}".format(self.name, suffix)
            )

        raise IOError("Shader '{}' not found".format(self.name))

    def load_from_source(self):
        """Loads the source code from the disk and performs all the preprocessing."""
        source = self.get_source()
        include_lines = INCLUDE_MATCH_PATTERN.search(source)
        while include_lines:
            included = ShaderFile(include_lines.group(1), INCLUDE)
            source = source.replace(
                "#include {};".format(include_lines.group(1)), included.read()
            )
            include_lines = INCLUDE_MATCH_PATTERN.search(source)

        self.uniforms = []
        self.headers = []
        self.code = []

        headers = True
        for i in source.split("\n"):
            if "uniform" in i:
                self.uniforms.append(" ".join(i.split()))
                headers = False
            elif headers:
                self.headers.append(i)
            else:
                self.code.append(i)

        # Hack to make the elements unique
        self.uniforms = list(set(self.uniforms))

    def read(self):
        """Gets the processed source code as a string."""
        self.load_from_source()
        return "\n".join(self.headers + self.uniforms + self.code)

    def get_program(self):
        """Returns the OpenGL program object compiled from this source file.

        This function should be the main interface to the ShaderFile class."""

        if self.program is None:
            self.program = gl.glCreateShader(self.shader_type)
            gl.glShaderSource(self.program, self.read())
            gl.glCompileShader(self.program)
            # Find compile errors
            if gl.glGetShaderiv(self.program, gl.GL_COMPILE_STATUS) != gl.GL_TRUE:
                raise ShaderCompileException(
                    (gl.glGetShaderInfoLog(self.program), self.read())
                )

        return self.program
