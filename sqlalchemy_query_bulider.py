#!/usr/bin/env python
import operator
import logging
import inspect

import sqlparse
import sqlalchemy
import pyparsing

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
        'not': sqlalchemy.not_,
        'and': sqlalchemy.and_,
        'or':  sqlalchemy.or_,
        #'xor': sqlalchemy.xor_
    }

    __primitives = (int, float, str, unicode, bool)

    def __init__(self, session):
        self.session = session

    def parseAndBuild(self, queryString):
        try:
            #logger.debug('Parsing: %s' % queryString)
            ast = sqlparse.parseString(queryString)
        except pyparsing.ParseException, err:
            msg = [
                'Parse Error: %s' % err,
                queryString,
                '-' * (err.col - 1) + '^',
            ]
            logger.error('\n'.join(msg))
            raise

        classNames = ast['tables']
        self.modelClass = self._getModelClass(classNames[0])
        logger.debug('FROM: %s -> %s' % (classNames, self.modelClass))
        query = self.session.query(self.modelClass)

        whereExpr = self._evalExpr(ast.where[0])
        logger.debug('WHERE: %s' % whereExpr)

        query = query.filter(whereExpr)

        return query

    def _getModelClass(self, className):
        klass = globals()[className]
        if not inspect.isclass(klass):
            raise ValueError('%s is not a class' % className)
        return klass

    def _evalExpr(self, expr):
        if isinstance(expr, sqlparse.UnaryOperator):
            oper = self.__operators.get(expr.op)
            if oper is None:
                raise ValueError('unknown unary operator: %s' % expr.op)
            return oper(self._evalExpr(expr.rhs))

        elif isinstance(expr, sqlparse.BinaryOperator):
            oper = self.__operators.get(expr.op)
            if oper is None:
                raise ValueError('unknown binary operator: %s' % expr.op)
            return oper(self._evalExpr(expr.lhs), self._evalExpr(expr.rhs))

        elif isinstance(expr, sqlparse.ListValue):
            #print 'list: %s' % expr.values
            return expr.values

        elif isinstance(expr, sqlparse.RangeValue):
            raise ValueError('range values not implemeneted yet')

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
    import sqlalchemy.orm, sqlalchemy.ext.declarative
    import itertools
    logging.basicConfig(level=logging.DEBUG)

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
        is_active = sqlalchemy.Column(sqlalchemy.Boolean)

        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

        def __str__(self):
            return '%s %s' % (self.first_name, self.last_name)

    # Add seed data
    Base.metadata.create_all()
    names = {
        'first': [
            'Chris',
            'John',
            'Bob'
        ],
        'last': [
            'Jacob',
            'Smith',
            'Lyon'
        ]
    }
    for first_name, last_name in itertools.product(names['first'], names['last']):
        session.add(User(
            first_name=first_name,
            last_name=last_name,
            is_active=(first_name == 'Chris')))

    # Query seed data
    userBuilder = QueryBuilder(session)
    query = userBuilder.parseAndBuild("""
        select * from User where
            not (last_name = 'Jacob' or
                (first_name != 'Chris' and last_name != 'Lyon')) and
            not is_active = 1
        """)
    for user in query.all():
        logger.info(user)
