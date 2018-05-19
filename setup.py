from setuptools import setup

setup(
    name="dent",
    version="0.0.15",
    description="A 3D game engine",
    author="Robert Spencer",
    license="MIT",
    packages=["dent", "dent.Shaders", "dent.pycfg"],
    package_data={"dent.Shaders": ["*/*/*.shd"]},
    scripts=[
        "bin/dent-messages",
        "bin/dent-init",
        "bin/dent-assets",
    ],
    install_requires=[
        "setuptools>=36.0.1",
        "numpy>=1.13.1",
        "imgui==0.0.2",
        "Pillow>=4.3.0",
        "PyOpenGL>=3.1.1a1",
        "PyYAML>=3.12",
        "scipy>=1.0.0",
        "pyassimp==4.1.0",
        "PyOpenAL>=0.7.0a1",
        "imageio>=2.3.0",
    ],
    dependency_links=[
        "git+https://github.com/assimp/assimp.git@f4fd5840b143b5e57cbb820e9804386d414b6bf3#egg=pyassimp-4.1.0&subdirectory=port/PyAssimp"
    ],
    zip_safe=False,
    test_suite="nose.collector",
    tests_require=["nose"],
)
