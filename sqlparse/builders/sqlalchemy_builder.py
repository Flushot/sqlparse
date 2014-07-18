#!/usr/bin/env python
import operator
import logging
import inspect

import sqlalchemy
from sqlalchemy.orm.session import Session

import sqlparse
from sqlparse import nodes
from sqlparse.visitors import IdentifierAndValueVisitor
from .base import QueryBuilder

logger = logging.getLogger(__name__)


class SqlAlchemyQueryVisitor(IdentifierAndValueVisitor):
    BINARY_OPERATORS = {
        '=': operator.eq,
        '!=': operator.ne,
        '<>': operator.ne,
        '<': operator.lt,
        '<=': operator.le,
        '>': operator.gt,
        '>=': operator.ge,
        'and': sqlalchemy.and_,
        '&&': sqlalchemy.and_,
        'or': sqlalchemy.or_,
        '||': sqlalchemy.or_,
        'in': lambda lhs, rhs: lhs.in_(rhs),
        'between': lambda lhs, rhs: lhs.between(rhs.begin, rhs.end),
        'like': lambda lhs, rhs: lhs.like(rhs),
        #'ilike': lambda lhs, rhs: lhs.ilike(rhs),  # TODO: implement in grammar

        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv,
        '%': operator.mod,
        '**': operator.pow,
        '<<': operator.lshift,
        '>>': operator.rshift
    }

    UNARY_OPERATORS = {
        '!':   sqlalchemy.not_,
        'not': sqlalchemy.not_,
        '~':   operator.inv,
        '-':   operator.neg,
        '+':   operator.pos
    }

    def __init__(self, model_class):
        self.model_class = model_class

    def visit_UnaryOperator(self, node):
        op_func = self.UNARY_OPERATORS.get(node.name)
        if op_func is None:
            raise ValueError('SqlAlchemy visitor does not implement "%s" unary operator')

        return op_func(self.visit(node.rhs))

    def visit_BinaryOperator(self, node):
        # XOR operator
        if node.name in ('xor', '^'):
            # SqlAlchemy doesn't support XOR operator
            lhs_node = self.visit(node.lhs)
            rhs_node = self.visit(node.rhs)
            return sqlalchemy.and_(
                sqlalchemy.or_(lhs_node, rhs_node),
                sqlalchemy.not_(
                    sqlalchemy.and_(lhs_node, rhs_node)))

        # Regular operator
        else:
            op_func = self.BINARY_OPERATORS.get(node.name)
            if op_func is None:
                raise ValueError('Mongo visitor does not implement "%s" binary operator' % node.name)

            return op_func(self.visit(node.lhs), self.visit(node.rhs))

    def visit_Identifier(self, node):
        # Ensure property is mapped in SqlAlchemy (and thus can be queried)
        mapped_properties = set([p.key for p in self.model_class.__mapper__.iterate_properties])
        if node.name not in mapped_properties:
            raise ValueError('%s property is not a mapped relation, and can not be queried with SqlAlchemy' % node.name)

        # Class property that can be used in SqlAlchemy query expressions
        return getattr(self.model_class, node.name)


class SqlAlchemyQueryBuilder(QueryBuilder):
    """
    Builds a SqlAlchemy query from a SQL query
    """
    def __init__(self, session, model_scope=None):
        super(SqlAlchemyQueryBuilder, self).__init__()

        if session is None:
            raise ValueError('session is required')
        if not isinstance(session, Session):
            raise ValueError('session must be a SqlAlchemy session object')

        # TODO: figure out if there's a way to do detached queries w/o depending on session (like hibernate)
        self.session = session

        if model_scope is None:
            model_scope = globals()

        self.model_scope = model_scope

    def parse_and_build(self, query_string):
        parse_tree = self._parse(query_string)

        self.model_class = self._get_model_class(parse_tree)

        self.fields = self._get_projection(parse_tree)
        query = self.session.query(self.model_class)

        criteria = self._get_filter_criteria(self.model_class, parse_tree)
        if criteria is not None:
            query = query.filter(criteria)

        return query

    def _get_model_class(self, parse_tree):
        class_names = [v.name for v in parse_tree.tables.values]
        if len(class_names) == 0:
            raise ValueError('Model name required in FROM clause')

        # TODO: support multiple classes and aliases
        if len(class_names) > 1:
            raise NotImplementedError('SqlAlchemy queries currently only support a single model class')

        class_name = class_names[0]
        #print 'FROM: %s' % class_name

        klass = self.model_scope.get(class_name)
        if klass is None:
            raise ValueError('Model class %s not found in model_scope' % class_name)
        elif not inspect.isclass(klass):
            raise ValueError('Model class %s is not a class' % class_name)

        return klass

    def _get_projection(self, parse_tree):
        projection = IdentifierAndValueVisitor().visit(parse_tree.columns)
        #print 'SELECT: %s' % projection
        if not isinstance(projection, list):
            raise ValueError('SELECT must be a list')

        return projection

    def _get_filter_criteria(self, model_class, parse_tree):
        filter_criteria =  SqlAlchemyQueryVisitor(model_class).visit(parse_tree.where[0])
        print 'WHERE: %s' % filter_criteria
        return filter_criteria
