#!/usr/bin/env python
import operator
import logging

import pyparsing
import sqlalchemy

import sqlparse
from .base import QueryBuilder

logger = logging.getLogger(__name__)


class SqlAlchemyQueryBuilder(QueryBuilder):
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
        try:
            #logger.debug('Parsing: %s' % queryString)
            ast = sqlparse.parseString(query_string)
        except pyparsing.ParseException, err:
            msg = [
                'Parse Error: %s' % err,
                query_string,
                '-' * (err.col - 1) + '^',
            ]
            logger.error('\n'.join(msg))
            raise
        
        # TODO: support multiple classes and aliases
        class_names = ast['tables']
        self.model_class = self._get_model_class(class_names[0])
        logger.debug('FROM: %s -> %s' % (class_names, self.model_class))
        query = self.session.query(self.model_class)

        where_expr = self._eval_expr(ast.where[0])
        logger.debug('WHERE: %s' % where_expr)

        query = query.filter(where_expr)

        return query

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

        elif isinstance(expr, sqlparse.sqlparse.ListValue):
            #print 'list: %s' % expr.values
            return expr.values

        elif isinstance(expr, sqlparse.sqlparse.RangeValue):
            raise ValueError('range values not implemeneted yet')

        elif type(expr) in (str, unicode):
            if len(expr) > 2 and expr[0] in ('"', "'"):
                # string
                return expr[1:-1]
            else:
                # identifier (assume prop on model)
                return getattr(self.model_class, expr)

        elif self._is_primitive(expr):
            #print 'prim: %s' % expr
            return expr

        else:
            raise ValueError('unknown expression type: %s' % type(expr))
