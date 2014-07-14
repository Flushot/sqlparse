#!/usr/bin/env python
import operator
import logging

import pyparsing
import pymongo

import sqlparse
from .base import QueryBuilder

logger = logging.getLogger(__name__)


class MongoQueryBuilder(QueryBuilder):
    def parse_and_build(self, query_string):
        raise NotImplementedError()
