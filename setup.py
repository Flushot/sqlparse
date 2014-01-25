#!/usr/bin/env python
#from distutils.core import setup
from setuptools import setup
import sqlparse

setup(
    name='sqlparse',
    version=sqlparse.__version__,

    author='Chris Lyon',
    author_email='flushot@gmail.com',
    long_description=open('README.md').read(),
    url='https://github.com/Flushot/sqlparse',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha'
    ],

    install_requires=[
        'sqlalchemy'
    ],
    test_suite = 'sqlparse'
)
