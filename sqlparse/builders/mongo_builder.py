#!/usr/bin/env python
import logging
import json

import sqlparse
from sqlparse import nodes
from sqlparse.visitors import IdentifierAndValueVisitor
from .base import QueryBuilder

logger = logging.getLogger(__name__)


class MongoQueryVisitor(IdentifierAndValueVisitor):
    # Map of SQL operators to MongoDB equivalents
    # TODO: Create node classes for these operators, rather than relying on operator.name
    OPERATORS = {
        'not': '$nor',
        '!': '$nor',
        '!=': '$ne',
        '<>': '$ne',
        '<': '$lt',
        '<=': '$lte',
        '>': '$gt',
        '>=': '$gte',
        'and': '$and',
        '&&': '$and',
        'or': '$or',
        '||': '$or',
        'in': '$in',
        'mod': '$mod',
        '%': '$mod',
        'like': '$regex',
        # Mongo doesn't support: + - * / ** << >>
    }

    def visit_UnaryOperator(self, node):
        op_name = self.OPERATORS.get(node.name)
        if op_name is None:
            raise ValueError('Mongo visitor does not implement "%s" unary operator')

        rhs_node = self.visit(node.rhs)
        if not isinstance(rhs_node, nodes.ListValue):
            rhs_node = [ rhs_node ]

        return { op_name: rhs_node }

    def visit_BinaryOperator(self, node):
        lhs_node = self.visit(node.lhs)
        rhs_node = self.visit(node.rhs)

        if node.name == '=':
            # Mongo treats equality struct different from other binary operators
            if isinstance(lhs_node, basestring):
                return { lhs_node: rhs_node }
            else:
                raise ValueError('lhs is an expression: %s' % lhs_node)

        elif node.name in ('xor', '^'):
            # Mongo lacks an XOR operator
            return {
                '$and': [
                    { '$or': [ lhs_node, rhs_node ] },
                    { '$and': [
                        { '$nor': [ lhs_node ] },
                        { '$nor': [ rhs_node ] }
                    ]}
                ]}

        elif node.name == 'between':
            # Mongo lacks a BETWEEN operator
            return {
                '$and': [
                    { lhs_node: { '$gte': rhs_node.begin } },
                    { lhs_node: { '$lte': rhs_node.end } }
                ]}

        # Standard binary operator
        else:
            op_name = self.OPERATORS.get(node.name)
            if op_name is None:
                raise ValueError('Mongo visitor does not implement "%s" binary operator' % node.name)

            # AND and OR have list operands
            if op_name in ('$and', '$or'):
                return { op_name: [ lhs_node, rhs_node ] }
            # Everything else contains a { prop: expr } operand
            elif isinstance(lhs_node, basestring):
                return { lhs_node: { op_name: rhs_node } }
            else:
                raise ValueError('lhs is an expression: %s' % lhs_node)


class MongoQueryBuilder(QueryBuilder):
    """
    Builds a MongoDB query from a SQL query
    """
    def parse_and_build(self, query_string):
        parse_tree = sqlparse.parse_string(query_string)
        filter_options = {}

        # collections
        self.model_class = self._get_collection_name(parse_tree)
        self.class_names = [ self.model_class ]

        # fields
        filter_fields = self._get_fields_option(parse_tree)
        self.fields = filter_fields.keys()
        if filter_fields:
            filter_options['fields'] = filter_fields

        return self._get_filter_criteria(parse_tree), filter_options

    def _get_filter_criteria(self, parse_tree):
        """
        Filter criteria specified in WHERE
        """
        filter_criteria =  MongoQueryVisitor().visit(parse_tree.where[0])
        #print 'WHERE: %s' % json.dumps(filter_criteria, indent=4)
        return filter_criteria

    def _get_collection_name(self, parse_tree):
        """
        Collections specified in FROM
        """
        collections = [unicode(table.name) for table in parse_tree.tables.values]
        if len(collections) == 0:
            raise ValueError('Collection name required in FROM clause')

        collection = collections[0]
        #print 'FROM: %s' % collection

        # TODO: parse this as an Identifier instead of a str
        if not isinstance(collection, basestring):
            raise ValueError('collection name must be a string')

        if len(collections) > 1:
            raise ValueError('Mongo query requires single collection in FROM clause')

        return collection

    def _get_fields_option(self, parse_tree):
        """
        Fields specified in SELECT
        """
        fields = IdentifierAndValueVisitor().visit(parse_tree.columns)
        #print 'SELECT: %s' % fields
        if not isinstance(fields, list):
            raise ValueError('SELECT must be a list')

        filter_fields = {}
        for field in fields:
            if field == '*':
                return {}

            filter_fields[field.name] = 1

        return filter_fields
