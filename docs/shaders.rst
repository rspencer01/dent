Shaders
=======

Shader objects in Dent represent complete shader programs: a vertex shader,
possibly tesselation shaders and geometry shader, and a fragment shader. They
are written in OpenGL Shader Language, with a small modification.

This guide assumes some knowledge of OpenGL shaders and pipelines. If you are
new to all this, it is suggested to copy one of the shaders from an existing
project and tweak it to your needs, or only use the builtin shaders.

======================== =================== ==============================
 Shader type             Filename            Required
======================== =================== ==============================
 Vertex                  ``vertex.shd``      Yes
 Geometry                ``geometry.shd``    No
 Tesselation control     ``tesscontrol.shd`` No
 Tesselation evaluation  ``tesseval.shd``    Only if control shader present
 Fragment                ``fragment.shd``    Yes
======================== =================== ==============================

A simple vertex shader might look like this::

  #version 400
  in vec3 position;
  out vec2 pos;

  uniform mat3 model;

  void main()
  {
    gl_Position = vec4((model * position.xyz), 1);
    pos = position.xy/2+0.5;
  }

The corresponding fragment shader might be::

  #version 400
  in vec2 pos;
  out vec4 fragColor;

  uniform sampler2D colormap;

  void main()
  {
    fragColor = texture(colormap, vec2(pos.x, 1-pos.y));
  }

Note the output of the fragment shader is a `vec4`.  You may output up to three vectors for defered rendering (see :doc:`render-pipelines`).

Shaders are stored in the game tree under the folder ``shaders``::

  game
    ├── my-awesome-game.py
    ├── scenes
    │   ├── __init__.py
    │   └── MainScene.py
    └── shaders
        ├── image
        │   ├── fragment.shd
        │   └── vertex.shd
        └── ...

A shader object is created easily.  For example to create a standard vertex-fragment shader and set some uniforms::

  import dent.Shaders

  ...

  shader = dent.Shaders.getShader('images')
  shader['some_uniform'] = 1.4
  shader['some_other_uniform'] = np.arange(1, 4, 0.3)

This corresponds to the ``shaders/image/*`` shader above.

The main function of shaders is the :code:`draw` method. This loads the shader, sets
the relevant uniforms and executes a :code:`glDraw*` command. The precice command
depends on the type of shader (generic, instanced, or feedback). Thus an object
in the scene typically has a :code:`display` function of the form::

  def display(self):
    self.shader['model'] = self.model
    self.shader.draw(gl.GL_TRIANGLES, self.renderID)

For more detail, see the API documentation of the :doc:`api/dent.Shaders`.
