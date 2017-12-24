from setuptools import setup

setup(name='dent',
    version='0.0.6',
    description='A 3D game engine',
    author='Robert Spencer',
    licence='MIT',
    packages=['dent', 'dent.Shaders', 'dent.pycfg'],
    package_data={
      'dent.Shaders': ['*/*/*.shd'],
    },
    scripts=['bin/dent-messages',
             'bin/dent-init'],
    zip_safe=False,
    test_suite='nose.collector',
    tests_require=['nose'],
    )
