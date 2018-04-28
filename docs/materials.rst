Materials
=========

Materials are nothing more than a glorified set of parameters to the rendering
software (shader).  In theory, the rendering system is simply::

  render(mesh, material)

where the mesh specifies the geometry, and the material everything else.

In practice, there are a number of different rendering systems and even more
model formats that store materials, and as such, the
:class:`~dent.Material.Material` class must cater to all of them.  Dent tries
to take a "catch-em-all" approach, where each material has as many parameters
as it can, and it is up to the renderer to discard that are not useful.

Parameters of a Material
------------------------

If you are writing a shader for the default Dent material system, you can expec
to be fed a number of textures and constants.  They are as listed at the bottom
of this document, with details.  In brief, though, they are:

=================== ================= ============= ===========================
parameter           uniform name      type          description
=================== ================= ============= ===========================
diffuse color tint  ``diffuse_tint``  ``vec3``      a constant by which to multiply the colormap
metallic tint       ``metallic_tint`` ``float``     a constant by which to multiply the metallic map
roughness tint      ``specular_tint`` ``float``     a constant by which to multiply the roughness map
color texture       ``colormap``      ``sampler2d`` the fragment diffuse/albedo value
normal texture      ``normalmap``     ``sampler2d`` the fragment normal map
specularity texture ``specularmap``   ``sampler2d`` the fragment specularity value
metallic texture    ``metallicmap``   ``sampler2d`` the fragment metallic value
roughness texture   ``roughnessmap``  ``sampler2d`` the fragment roughness value
=================== ================= ============= ===========================

As you can see, this covers most of the required inputs to Blinn-Phong or
Cook-Torrance BDRFs, and so can be used with the builtin lighting shaders.

Parsing Materials from Models
-----------------------------

Importing materials is a pain for two reasons.  The first is that, unlike
meshes, there's no consensus on what information should be stored with an
object with regard to its materials.  The second is the way that ``pyassimp``
deals with this problem: it doesn't.

As a result, under the hood, Dent has to do some fancy footwork to guess the
right parameters for the material.  This unfortunately may require some work
from the artist/developer.  The exact specifics of the defaults chosen are
detailed below.

Parameters
----------

All texture maps described below can be overridden (see :ref:`overriding-textures`).

Diffuse and Albedo
^^^^^^^^^^^^^^^^^^

Most shaders require some sort of colour data.  For Phong shaders, this is the
diffuse colour.  For PBR it is known as the albedo.

In Dent this data is passed as the diffuse colour tint and the colour texture.
The correct way to compute the actual value is to multiply the two together.

The default for the image is a blank white texture.  The default for the colour
is the assimp default of all black.  The tint can be specified in any way that is parsed to the ``COLOR_DIFFUSE`` property of assimp, and the map in any way that can be parsed to the first texture in the diffuse stack.  As an example, in ``OBJ`` material format::

  newmtl my_material
  Kd 0.640000 0.640000 0.640000
  map_Kd color.tga

Normal Maps
^^^^^^^^^^^

Normal maps are also stored as part of materials.  They are only stored as textures.

The default texture is a single ``(0,0,1)`` valued ``(r,g,b)`` texture.  Any map passed to the first layer of the normal stack of assimp is valid, as is any map passed to the first layer of the bump map.  As an example in ``OBJ`` material format::

  newmtl my_material
  map_Bump normal.tga.

Phong Specific Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^

The specularity is a measure of the coefficient of specularity in Blinn-Phong
lighting.  It is stored as a texture only.  Any map passed to the first layer of the specular stack of assimp is valid.  As an example in ``OBJ`` material format::

  newmtl my_material
  map_Ks specular.tga


PBR Specific Parameters
^^^^^^^^^^^^^^^^^^^^^^^

The parameters of roughness and metallic are specific to PBR shading.  They are
stored in the roughness texture and tint, and the metallic texture and tint
parameters.  Again, the correct value is obtained by multiplying the two.

Currenly the only way to set these textures is to override them.  The tints
default to 1.

.. _overriding-textures:

Overriding Textures
-------------------

Any of the above textures can be overridden, by placing appropriate image files
in the same directory as the model.  The format for the image filename is
``{material_name}.{suffix}.png``, where the ``{suffix}`` is given from the
below table

============ ========
Texture type Suffix
============ ========
Diffuse      ``diff``
Normal       ``norm``
Specular     ``spec``
Roughness    ``roug``
Metallic     ``meta``
============ ========

Debugging Materials
-------------------

You can use the Dent asset inspector to view materials and their properties,
once they have been loaded into an asset datastore.  This is useful to study
the values for the tints and textures that are actually parsed by Dent.  To do
this, run ``dent-assets inspect``, and navigate to the material in question and
hit enter to examine its properties.

API
---

.. automodule:: dent.Material
    :members:
    :undoc-members:
    :show-inheritance:
