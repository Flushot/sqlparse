#!/usr/bin/env python
#from distutils.core import setup
from setuptools import setup
from sys import version
if version < '2.2.3':
    # allow trove classifiers in previous python versions
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None

import sqlparse

setup(
    name='sqlparse',
    version=sqlparse.__version__,

    author='Chris Lyon',
    author_email='flushot@gmail.com',
    description='SQL parser and query builders',
    long_description=open('README.md').read(),
    url='https://github.com/Flushot/sqlparse',
    license='Apache License 2.0',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers'
    ],

    install_requires=[
        'pyparsing'
        #'sqlalchemy'
    ],

    test_suite='sqlparse'
)
