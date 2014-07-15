#!/usr/bin/env python
import operator
import logging
import inspect

import pyparsing
import sqlalchemy

import sqlparse
from .base import QueryBuilder

logger = logging.getLogger(__name__)


class SqlAlchemyQueryBuilder(QueryBuilder):
    """
    Builds a SqlAlchemy query from a SQL query
    """
    _binary_operators = {
        '=':   operator.eq,
        '!=':  operator.ne,
        '<>':  operator.ne,
        '<':   operator.lt,
        '<=':  operator.le,
        '>':   operator.gt,
        '>=':  operator.ge,
        'and': sqlalchemy.and_,
        '&&':  sqlalchemy.and_,
        'or':  sqlalchemy.or_,
        '||':  sqlalchemy.or_,
        'xor': operator.xor,
        '^':   operator.xor,
        'in':  lambda lhs, rhs: lhs.in_(rhs),
        'between': lambda lhs, rhs: lhs.between(rhs.begin, rhs.end),

        '+':   operator.add,
        '-':   operator.sub,
        '*':   operator.mul,
        '/':   operator.truediv,
        '%':   operator.mod,
        '**':  operator.pow,
        '<<':  operator.lshift,
        '>>':  operator.rshift
    }

    _unary_operators = {
        '!':   sqlalchemy.not_,
        'not': sqlalchemy.not_,
        '~':   operator.inv,
        '-':   operator.neg,
        '+':   operator.pos
    }

    def parse_and_build(self, query_string):
        ast = self._parse(query_string)

        # TODO: support multiple classes and aliases
        class_names = ast['tables']
        if len(class_names) > 1:
            raise ValueError('queries only support a single model class')

        self.model_class = self._get_model_class(class_names[0])
        logger.debug('FROM: %s -> %s' % (class_names, self.model_class))

        criteria = self._eval_expr(ast.where[0])
        logger.debug('WHERE: %s' % criteria)

        query = self.session.query(self.model_class)
        query = query.filter(criteria)
        return query

    def _get_model_class(self, class_name):
        klass = self.model_scope[class_name]
        if not inspect.isclass(klass):
            raise ValueError('%s is not a class' % class_name)

        return klass

    def _eval_expr(self, expr):
        # TODO: type checking
        if isinstance(expr, sqlparse.opers.UnaryOperator):
            oper = self._unary_operators.get(expr.op)
            if oper is None:
                raise ValueError('Unary %s operator is not supported in SqlAlchemy dialect' % expr.op)
            return oper(self._eval_expr(expr.rhs))

        elif isinstance(expr, sqlparse.opers.BinaryOperator):
            oper = self._binary_operators.get(expr.op)
            if oper is None:
                raise ValueError('Binary %s operator is not supported in SqlAlchemy dialect' % expr.op)
            return oper(self._eval_expr(expr.lhs), self._eval_expr(expr.rhs))

        # elif isinstance(expr, sqlparse.sqlparse.ListValue):
        #     #print 'list: %s' % expr.values
        #     return expr.values
        #
        # elif isinstance(expr, sqlparse.sqlparse.RangeValue):
        #     raise ValueError('range values not implemeneted yet')

        elif type(expr) in (str, unicode):
            if len(expr) > 2 and expr[0] in ('"', "'"):
                # string
                return expr[1:-1]
            else:
                # identifier (assume prop on model)
                prop = getattr(self.model_class, expr)
                if str(expr) not in set([p.key for p in self.model_class.__mapper__.iterate_properties]):
                    raise ValueError('%s property is not a mapped relation, and can not be queried with SqlAlchemy' % expr)
                return prop

        elif self._is_primitive(expr):
            #print 'prim: %s' % expr
            return expr

        else:
            raise ValueError('Unknown expression type: %s' % type(expr))
