#!/usr/bin/env python
import operator
import logging
import inspect

import pyparsing
import pymongo

import sqlparse
from .base import QueryBuilder

logger = logging.getLogger(__name__)


class MongoQueryBuilder(QueryBuilder):
    """
    Builds a MongoDB query from a SQL query
    """
    # mongo doesn't have an xor operator
    _xor_operator = lambda lhs, rhs: {
            '$and': [
                { '$or': [ lhs, rhs ] },
                { '$and': [
                    { '$nor': [ lhs ] },
                    { '$nor': [ rhs ] }
                ]}
            ]}

    _binary_operators = {
        '=':   lambda lhs, rhs: { lhs: rhs },
        '!=':  lambda lhs, rhs: { lhs: { '$ne': rhs } },
        '<>':  lambda lhs, rhs: { lhs: { '$ne': rhs } },
        '<':   lambda lhs, rhs: { lhs: { '$lt': rhs } },
        '<=':  lambda lhs, rhs: { lhs: { '$lte': rhs } },
        '>':   lambda lhs, rhs: { lhs: { '$gt': rhs } },
        '>=':  lambda lhs, rhs: { lhs: { '$gte': rhs } },
        'and': lambda lhs, rhs: { '$and': [ lhs, rhs ] },
        '&&':  lambda lhs, rhs: { '$and': [ lhs, rhs ] },
        'or':  lambda lhs, rhs: { '$or': [ lhs, rhs ] },
        '||':  lambda lhs, rhs: { '$or': [ lhs, rhs ] },
        'xor': _xor_operator,
        '^':   _xor_operator,
        'in':  lambda lhs, rhs: { lhs: { '$in': rhs } },

        # mongo doesn't have a between operator
        'between': lambda lhs, rhs: {
                '$and': [
                    { lhs: { '$gte': rhs.begin } },
                    { lhs: { '$lte': rhs.end } }
                ]
            },

        # TODO: convert like/ilike wildcards to regex
        #'like': lambda lhs, rhs: { lhs: { "$regex": rhs } }
        #'ilike': ...

        '%':   lambda lhs, rhs: { '$mod': [ lhs, rhs ] }

        # unsupported by mongo: xor between + - * / ** << >>
    }

    _unary_operators = {

        # $nor w/ single arg is used instead of $not (which can only be used as a RHS binary operator)
        '!':   lambda rhs: { "$nor": [ rhs ] },
        'not': lambda rhs: { "$nor": [ rhs ] },

        # unsupported by mongo: ~ - +
    }

    def parse_and_build(self, query_string):
        ast = sqlparse.parse_string(query_string)

        # TODO: support multiple classes and aliases
        class_names = ast['tables']
        if len(class_names) > 1:
            raise ValueError('Queries only support a single model class')

        self.model_class = class_names[0]
        logger.debug('FROM: %s -> %s' % (class_names, self.model_class))

        criteria = self._eval_expr(ast.where[0])
        logger.debug('WHERE: %s' % criteria)

        return criteria, None

    def _eval_expr(self, expr):
        # TODO: type checking
        if isinstance(expr, sqlparse.opers.UnaryOperator):
            oper = self._unary_operators.get(expr.op)
            if oper is None:
                raise ValueError('Unary %s operator is not supported in Mongo dialect' % expr.op)
            return oper(self._eval_expr(expr.rhs))

        elif isinstance(expr, sqlparse.opers.BinaryOperator):
            oper = self._binary_operators.get(expr.op)
            if oper is None:
                raise ValueError('Binary %s operator is not supported in Mongo dialoect' % expr.op)
            return oper(self._eval_expr(expr.lhs), self._eval_expr(expr.rhs))

        # elif isinstance(expr, sqlparse.sqlparse.ListValue):
        #     #print 'list: %s' % expr.values
        #     return expr.values

        # elif isinstance(expr, sqlparse.sqlparse.RangeValue):
        #     raise ValueError('range values not implemeneted yet')

        elif type(expr) in (str, unicode):
            if len(expr) > 2 and expr[0] in ('"', "'"):
                # string
                return expr[1:-1]
            else:
                # identifier (assume prop on model)
                return expr

        elif self._is_primitive(expr):
            #print 'prim: %s' % expr
            return expr

        else:
            raise ValueError('Unknown expression type: %s' % type(expr))
