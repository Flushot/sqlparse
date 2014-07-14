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
    _binary_operators = {
        '=':   lambda lhs, rhs: { lhs: rhs },
        '!=':  lambda lhs, rhs: { lhs: { "$ne": rhs } },
        '<>':  lambda lhs, rhs: { lhs: { "$ne": rhs } },
        '<':   lambda lhs, rhs: { lhs: { "$lt": rhs } },
        '<=':  lambda lhs, rhs: { lhs: { "$lte": rhs } },
        '>':   lambda lhs, rhs: { lhs: { "$gt": rhs } },
        '>=':  lambda lhs, rhs: { lhs: { "$gte": rhs } },
        'and': lambda lhs, rhs: { "$and": [ lhs, rhs ] },
        '&&':  lambda lhs, rhs: { "$and": [ lhs, rhs ] },
        'or':  lambda lhs, rhs: { "$or": [ lhs, rhs ] },
        '||':  lambda lhs, rhs: { "$or": [ lhs, rhs ] },
        #'xor': lambda lhs, rhs: { "$xor": [ lhs, rhs ] },
        #'^':   lambda lhs, rhs: { "$xor": [ lhs, rhs ] },
        'in':  lambda lhs, rhs: { lhs: { "$in": rhs } },

        # '+':   operator.add,
        # '-':   operator.sub,
        # '*':   operator.mul,
        # '/':   operator.truediv,
        # '%':   operator.mod,
        # '**':  operator.pow,
        # '<<':  operator.lshift,
        # '>>':  operator.rshift
    }

    _unary_operators = {
        '!':   lambda rhs: { "$nor": [ rhs ] },
        'not': lambda rhs: { "$nor": [ rhs ] },
        # '~':   operator.inv,
        # '-':   operator.neg,
        # '+':   operator.pos
    }

    def parse_and_build(self, query_string):
        ast = sqlparse.parseString(query_string)

        # TODO: support multiple classes and aliases
        class_names = ast['tables']
        if len(class_names) > 1:
            raise ValueError('queries only support a single model class')

        self.model_class = class_names[0]
        logger.debug('FROM: %s -> %s' % (class_names, self.model_class))

        criteria = self._eval_expr(ast.where[0])
        logger.debug('WHERE: %s' % criteria)

        return criteria, None

    def _eval_expr(self, expr):
        # TODO: type checking
        if isinstance(expr, sqlparse.sqlparse.UnaryOperator):
            oper = self._unary_operators.get(expr.op)
            if oper is None:
                raise ValueError('unknown unary operator: %s' % expr.op)
            return oper(self._eval_expr(expr.rhs))

        elif isinstance(expr, sqlparse.sqlparse.BinaryOperator):
            oper = self._binary_operators.get(expr.op)
            if oper is None:
                raise ValueError('unknown binary operator: %s' % expr.op)
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
                # TODO: ensure expr is a mapped property that can be queried
                return expr

        elif self._is_primitive(expr):
            #print 'prim: %s' % expr
            return expr

        else:
            raise ValueError('unknown expression type: %s' % type(expr))
