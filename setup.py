from setuptools import setup

setup(name='dent',
    version='0.0.4',
    description='A 3D game engine',
    author='Robert Spencer',
    licence='MIT',
    packages=['dent', 'dent.Shaders', 'dent.pycfg'],
    scripts=['bin/dent-messages',
             'bin/dent-init'],
    zip_safe=False)
