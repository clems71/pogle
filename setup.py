#!/usr/bin/env python

from setuptools import setup
from Cython.Build import cythonize

setup(
    name = 'Python OpenGL Engine',
    version = '0.1',
    author = 'Clement Jacob',
    author_email = 'clems71@gmail.com',
    description = ('A simplistic OpenGL engine for python'),
    url='https://github.com/clems71/pogle',
    license = 'MIT',
    ext_modules = cythonize('pogle/*.pyx'),
    keywords = 'opengl',
    packages=['pogle', ],
    package_dir={'pogle': 'pogle'},
    install_requires = ['pyopengl', 'numpy', 'pillow', 'pyglfw', 'cython'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: MIT License',
    ],
)
