from setuptools import setup

setup(name='dent',
    version='0.0.2',
    description='A 3D game engine',
    author='Robert Spencer',
    licence='MIT',
    packages=['dent', 'dent.Shaders', 'dent.pycfg'],
    scripts=['bin/dent-messages'],
    zip_safe=False)
