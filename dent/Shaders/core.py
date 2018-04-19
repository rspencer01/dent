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
                    ShaderFile(name, gl.GL_FRAGMENT_SHADER),
                    ShaderFile(name, gl.GL_VERTEX_SHADER),
                    geom and ShaderFile(name, gl.GL_GEOMETRY_SHADER),
                )
            else:
                shaders[name] = InstancedShader(
                    name,
                    ShaderFile(name, gl.GL_FRAGMENT_SHADER),
                    ShaderFile(name, gl.GL_VERTEX_SHADER),
                    geom and ShaderFile(name, gl.GL_GEOMETRY_SHADER),
                )
        else:
            shaders[name] = TesselationShader(
                name,
                ShaderFile(name, gl.GL_FRAGMENT_SHADER),
                ShaderFile(name, gl.GL_VERTEX_SHADER),
                geom and ShaderFile(name, gl.GL_GEOMETRY_SHADER),
                ShaderFile(name, gl.GL_TESS_CONTROL_SHADER),
                ShaderFile(name, gl.GL_TESS_EVALUATION_SHADER),
            )
        setUniversalUniforms(shaders[name])
    return shaders[name]


def setUniform(name, value):
    for i in shaders:
        shaders[i][name] = value


def reload_all():
    for shader in shaders.values():
        shader.reload()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Magrathea shader source inspector.")
    parser.add_argument("file", help="source file")
    args = parser.parse_args()

    print(getShaderFile(args.file, None).getSource())
