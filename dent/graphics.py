import OpenGL.GLUT as glut
import OpenGL.GL as gl
import sys
import logging
import messaging


def glut_reshape_handler(width, height):
    messaging.add_message(messaging.Message("window_reshape", (width, height)))


def initialise_graphics():
    logging.info("Initialising OpenGL Graphics")

    glut.glutInit(sys.argv)

    logging.debug("Requesting OpenGL 4.2")

    glut.glutInitContextVersion(4, 2)
    glut.glutInitContextFlags(glut.GLUT_FORWARD_COMPATIBLE)
    glut.glutInitContextProfile(glut.GLUT_CORE_PROFILE)
    glut.glutInitDisplayMode(
        glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH | glut.GLUT_MULTISAMPLE
    )
    glut.glutInitWindowSize(512, 512)
    glut.glutCreateWindow("Dent")
    glut.glutSetKeyRepeat(glut.GLUT_KEY_REPEAT_OFF)
    glut.glutIgnoreKeyRepeat(1)
    glut.glutSetCursor(glut.GLUT_CURSOR_NONE)

    glut.glutReshapeFunc(glut_reshape_handler)

    logging.debug("Obtained OpenGL " + gl.glGetString(gl.GL_VERSION))
    logging.debug(
        "Uniform limit (vertex) {}".format(
            str(gl.glGetIntegerv(gl.GL_MAX_VERTEX_UNIFORM_COMPONENTS))
        )
    )
    logging.debug(
        "Tesselation limit {}".format(str(gl.glGetIntegerv(gl.GL_MAX_TESS_GEN_LEVEL)))
    )

    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
    gl.glEnable(gl.GL_BLEND)
    gl.glEnable(gl.GL_MULTISAMPLE)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    gl.glCullFace(gl.GL_BACK)
