#!/usr/bin/env python
import operator
import logging

import sqlparse
import sqlalchemy

logger = logging.getLogger(__name__)


class QueryBuilder(object):
    __operators = {
        '=':   operator.eq,
        '!=':  operator.ne,
        '<':   operator.lt,
        '<=':  operator.le,
        '>':   operator.gt,
        '>=':  operator.ge,
        '!':   sqlalchemy.not_,
        'and': sqlalchemy.and_,
        'or':  sqlalchemy.or_,
    }

    __primitives = (int, float, str, unicode, bool)

    def __init__(self, session, modelClass):
        self.session = session
        self.modelClass = modelClass

    def parseAndBuild(self, queryString):
        logger.info('parsing: %s' % queryString)

        query = self.session.query(self.modelClass)
        qtree = sqlparse.parseString(queryString)

        rootExpr = self._evalExpr(qtree.where[0])
        logger.debug('rootExpr: %s' % rootExpr)

        query = query.filter(rootExpr)

        return query

    def _evalExpr(self, expr):
        if isinstance(expr, sqlparse.UnaryOperator):
            raise ValueError('unary operators not supported')

        elif isinstance(expr, sqlparse.BinaryOperator):
            oper = self.__operators.get(expr.op)
            if oper is None:
                raise ValueError('unknown operator: %s' % expr.op)
            return oper(self._evalExpr(expr.lhs), self._evalExpr(expr.rhs))

        elif isinstance(expr, sqlparse.ListValue):
            #print 'list: %s' % expr.values
            return expr.values

        elif isinstance(expr, sqlparse.RangeValue):
            return range(expr.start, expr.end)  # Supported by sqlalchemy?

        elif type(expr) in (str, unicode):
            if len(expr) > 2 and expr[0] in ('"', "'"):
                # string
                return expr[1:-1]
            else:
                # identifier (assume prop on model)
                return getattr(self.modelClass, expr)

        elif type(expr) in self.__primitives:
            #print 'prim: %s' % expr
            return expr

        else:
            raise ValueError('unknown expression type: %s' % type(expr))


if __name__ == '__main__':
    from pprint import pprint
    import sqlalchemy.orm, sqlalchemy.ext.declarative

    # Testing
    engine = sqlalchemy.create_engine('sqlite://', echo=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    Base = sqlalchemy.ext.declarative.declarative_base(bind=engine)

    class User(Base):
        __tablename__ = 'users'

        id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
        first_name = sqlalchemy.Column(sqlalchemy.String)
        last_name = sqlalchemy.Column(sqlalchemy.String)

        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    # Add seed data
    Base.metadata.create_all()
    session.add(User(first_name='Chris', last_name='Lyon'))
    session.add(User(first_name='Chris', last_name='Smith'))

    # Query seed data
    userBuilder = QueryBuilder(session, User)
    query = userBuilder.parseAndBuild('select * from User where first_name = "Chris" and last_name = "Lyon"')
    for user in query.all():
        pprint(user)
