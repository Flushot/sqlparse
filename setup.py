#!/usr/bin/env python
from setuptools import setup, find_packages

import sqlparse

setup(
    name='sqlparse',
    version=sqlparse.__version__,

    author='Chris Lyon',
    author_email='flushot@gmail.com',

    description='SQL parser and query builder',
    long_description=open('README.md').read(),

    url='https://github.com/Flushot/sqlparse',

    packages=find_packages(include=["sqlparse", "sqlparse.*"]),
    
    license='Apache License 2.0',
    classifiers=[
        'Intended Audience :: Developers'
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: Apache Software License',
    ],

    install_requires=[
        'pyparsing',
        'sqlalchemy',
        'pymongo'
    ],

    test_suite='sqlparse'
)
