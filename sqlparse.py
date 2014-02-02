#!/usr/bin/env python
__version__ = '0.1'

import os
import sys
import operator
import collections
import unittest

import sqlalchemy
import pyparsing
from pyparsing import \
    Forward, Group, Combine, Suppress, StringEnd, \
    Optional, ZeroOrMore, OneOrMore, oneOf, \
    operatorPrecedence, opAssoc, \
    Word, Literal, CaselessLiteral, Regex, \
    alphas, nums, alphanums, quotedString, \
    restOfLine, quotedString, delimitedList, \
    ParseResults, ParseException

################################
# Terminals
################################

# Keywords
WHERE = CaselessLiteral('where')
FROM = CaselessLiteral('from')

SELECT = CaselessLiteral('select')
SELECT_DISTINCT = CaselessLiteral('distinct')
SELECT_ALL = CaselessLiteral('all')
AS = CaselessLiteral('as')

WITH = CaselessLiteral('with')
RECURSIVE = CaselessLiteral('recursive')

PIVOT = CaselessLiteral('pivot')
#UNPIVOT = CaselessLiteral('unpivot')
PIVOT_IN = CaselessLiteral('in')
PIVOT_FOR = CaselessLiteral('for')

ORDER_BY = CaselessLiteral('order by')
ORDER_ASC = CaselessLiteral('asc')
ORDER_DESC = CaselessLiteral('desc')

# Special values
VAL_NULL = CaselessLiteral('null')
VAL_TRUE = CaselessLiteral('true')
VAL_FALSE = CaselessLiteral('false')
VAL_UNKNOWN = CaselessLiteral('unknown')

# Joins
# JOIN = CaselessLiteral('join')
# OUTER = CaselessLiteral('outer')
# INNER = CaselessLiteral('inner')
# LEFT_JOIN = CaselessLiteral('left') + Optional(OUTER) + JOIN
# RIGHT_JOIN = CaselessLiteral('right') + Optional(OUTER) + JOIN
# INNER_JOIN = CaselessLiteral(INNER) + JOIN
# UNION = CaselessLiteral('union')
# UNION_ALL = UNION + CaselessLiteral('all')
# GROUP_BY = CaselessLiteral('group by')
# HAVING = CaselessLiteral('having')
# ORDER_BY = CaselessLiteral('order by')

# Operators (name is operators.FUNC_NAME)
OP_EQUAL = Literal('=').setParseAction(lambda t: operator.eq)
OP_VAL_NULLSAFE_EQUAL = Literal('<=>').setParseAction(lambda t: operator.eq)
OP_NOTEQUAL = ( Literal('!=') | Literal('<>') ).setParseAction(lambda t: operator.ne)
OP_GT = Literal('>').setName('gt').setParseAction(lambda t: operator.gt)
OP_LT = Literal('<').setName('lt').setParseAction(lambda t: operator.lt)
OP_GTE = Literal('>=').setName('ge').setParseAction(lambda t: operator.ge)
OP_LTE = Literal('<=').setName('le').setParseAction(lambda t: operator.le)
OP_IN = CaselessLiteral('in')  # sqlalchemy property: lhs.in_(rhs)
OP_LIKE = CaselessLiteral('like')  # sqlalchemy property: lhs.like(rhs), lhs.ilike(rhs)
OP_IS = CaselessLiteral('is')  # sqlalchemy or_(lhs == rhs, lhs == None)
OP_BETWEEN = CaselessLiteral('between')  # sqlalchemy: between
OP_BETWEEN_AND = Suppress( CaselessLiteral('and') )

# Math
# OP_ADD = Literal('+')
# OP_SUB = Literal('-')
# OP_MUL = Literal('*')
# OP_DIV = ( Literal('/') | CaselessLiteral('div') )
# OP_EXP = Literal('**')  # standard?
# addOp = OP_ADD | OP_SUB
# multOp = OP_MUL | OP_DIV
# OP_SHL = Literal('<<')
# OP_SHR = Literal('>>')

# Bitwise Operators
# BITOP_AND = Literal('&')
# BITOP_OR = Literal('|')
# BITOP_NOT = Literal('~')  # unary
# BITOP_XOR = Literal('^')

# Conjugates
LOGOP_AND = ( CaselessLiteral('and') | CaselessLiteral('&&') ).setParseAction(lambda t: sqlalchemy.and_)
LOGOP_OR =  ( CaselessLiteral('or')  | CaselessLiteral('||') ).setParseAction(lambda t: sqlalchemy.or_)
LOGOP_NOT = ( CaselessLiteral('not') | CaselessLiteral('!')  ).setParseAction(lambda t: sqlalchemy.not_)  # unary
LOGOP_XOR = CaselessLiteral('xor')#.setParseAction(lambda t: lambda a, b:
    #sqlalchemy.and_(sqlalchemy.or_(a, b), sqlalchemy.not_(sqlalchemy.and_(a, b))))

# SELECT Statement Operators
SELECTOP_EXCEPT = CaselessLiteral('except')
SELECTOP_INTERSECT = CaselessLiteral('intersect')
SELECTOP_UNION = CaselessLiteral('union')
SELECTOP_UNION_ALL = CaselessLiteral('all')

# Grouping
L_PAREN = Suppress('(')
R_PAREN = Suppress(')')

# Math
E = CaselessLiteral('e')
STAR = Literal('*')
DOT = Literal('.')
PLUS = Literal('+')
MINUS = Literal('-')

################################
# Non-Terminals
################################

# TODO: WITH ( RECURSIVE )

sign = PLUS | MINUS

selectStmt = Forward()  # SELECT

identifier = Word( alphas, alphanums + '_$' ).setName('identifier')  # a, A1, a_1$
#alias = ( Optional(AS) + identifier ).setName('alias')

# Projection
columnName = delimitedList( identifier, DOT, combine=True )('column')  # TODO: x AS y, x y, x `y`, x 'y', `x`, 'x'
columnNameList = Group( delimitedList( STAR | columnName ) )
tableName = delimitedList( identifier, DOT, combine=True )('table')
tableNameList = Group( delimitedList( tableName ) )

whereExpr = Forward()  # WHERE

# TODO: indirect comparisons (e.g. "table1.field1.xyz = 3" becomes "table1.any(field1.xyz == 3)")
# TODO: math expression grammar (for both lval and rval)
equalityOp = (
    OP_VAL_NULLSAFE_EQUAL ^
    OP_EQUAL ^
    OP_NOTEQUAL ^
    OP_LT ^
    OP_GT ^
    OP_GTE ^
    OP_LTE
    )
likeOp = (
    ( Optional(LOGOP_NOT) + OP_LIKE )
    )
betweenOp = Optional(LOGOP_NOT) + OP_BETWEEN  # [ NOT ] BETWEEN
realNumber = (
    Combine(
        Optional(sign) + (
            # decimal present
            ( ( Word(nums) + DOT + Optional(Word(nums)) | ( DOT + Word(nums) ) ) +
                Optional( E + Optional(sign) + Word(nums) ) ) |
            # negative exp
            ( Word(nums) + Optional( E + Optional(MINUS) + Word(nums) ) )
            )
        ).setParseAction( lambda token: float(token[0]) )
    ).setName('real')  # .1, 1.2, 1.2e3, -1.2e+3, 1.2e-3
intNumber = (
    Combine(
        Optional(sign) +
        Word(nums)
        #Optional( E + Optional(PLUS) + Word(nums) )  # python int() doesn't grok this
        ).setParseAction( lambda token: int(token[0]) )
    ).setName('int')  # -1 0 1 23
number = intNumber ^ realNumber
atom = (
    number |
    quotedString.setName('string').setParseAction( lambda t: '"%s"' % t[0][1:-1] )  # normalize quotes
    )
groupSubSelectStmt = Group( R_PAREN + selectStmt + R_PAREN )  # todo: subselect must have a LIMIT in this context
columnRval = (
    atom('value') |
    columnName('column') |
    groupSubSelectStmt('query')
    )
likePattern = (
    quotedString('value')
    )
# TODO: Functions: sum, avg, count, max, min, ifnull/isnull, if
#            current_date, current_time, current_timestamp, current_user
#            substring, regex, concat, group_concat
#            cast, convert
whereCond = (
    Optional(LOGOP_NOT('op')) +
    Group(
        ( columnName('column') + equalityOp('op') + columnRval ) |  # x = y, x != y, etc.
        ( columnName('column') + likeOp('op') + likePattern ) |
        ( columnName('column') + betweenOp('op') + Group( columnRval + OP_BETWEEN_AND + columnRval )('range') ) |  # x between y and z, x not between y and z
        ( columnName('column') + ( OP_IS + Optional(LOGOP_NOT) )('op') + ( VAL_NULL | VAL_TRUE | VAL_FALSE | VAL_UNKNOWN )('value') ) |  # x is null, x is not null
        ( columnName('column') + ( Optional(LOGOP_NOT) + OP_IN )('op') +
            Group( L_PAREN + delimitedList(columnRval) + R_PAREN | groupSubSelectStmt )('values') )
        )('expr') |
    ( L_PAREN + whereExpr('expr') + R_PAREN )
    )

class UnaryOperator(object):
    def __init__(self, tokens):
        self.op, self.rhs = tokens[0]

    def __repr__(self):
        return '%s %s' % (self.op, self.rhs)


class BinaryOperator(object):
    def __init__(self, tokens):
        self.lhs, self.op, self.rhs = tokens[0]

    def __repr__(self):
        return '%s %s %s' % (self.lhs, self.op, self.rhs)


# logOp = operatorPrecedence(
#     whereExpr('expr'), [
#         (LOGOP_NOT, 1, opAssoc.RIGHT, UnaryOperator),
#         (LOGOP_AND, 2, opAssoc.RIGHT, BinaryOperator),
#         (LOGOP_OR,  2, opAssoc.RIGHT, BinaryOperator)
#     ])
whereExpr << (
    Group( whereCond ) ^
    Group(
        whereCond +
        OneOrMore(
            LOGOP_AND('op') + whereExpr('expr') |
            LOGOP_XOR('op') + whereExpr('expr') |
            LOGOP_OR('op') + whereExpr('expr')
        )
    )
    )

columnProjection = (
    Optional( SELECT_DISTINCT | SELECT_ALL ).setResultsName('modifier') +
    columnNameList('columns')
    )

fromClause = Suppress(FROM) + tableNameList('tables')

# TODO: ( LEFT | RIGHT ) ( INNER | OUTER ) JOIN

# TODO: PIVOT, UNPIVOT
pivotClause = Optional(
    Group(
        PIVOT + L_PAREN + Group(columnNameList) +
        PIVOT_FOR + columnName +
        PIVOT_IN + Group(columnNameList) +
        R_PAREN )
    )('pivot')

whereClause = Optional( Suppress(WHERE) + whereExpr )('where')

# TODO: GROUP BY
# TODO: HAVING
# TODO: LIMIT, OFFSET (not really necessary, as this is determined by pager)

# ORDER BY x, y ASC, d DESC, ...
orderDirection = ORDER_ASC | ORDER_DESC
orderByColumnList = Group( delimitedList( columnName('column') + Optional(orderDirection)('direction') ) )
orderByClause = Optional( Suppress(ORDER_BY) + orderByColumnList('order') )  # todo: asc, desc

selectStmt << (
    Suppress(SELECT) +
    columnProjection +
    Optional(
        fromClause +
        #pivotClause +
        whereClause
        )
    #orderByClause
    )

# UNION ( ALL )
unionOp = Combine( SELECTOP_UNION + Optional(SELECTOP_UNION_ALL) )

# SELECT ... ( UNION | INTERSECT | EXCEPT ) SELECT ...
selectStmts = selectStmt + ZeroOrMore( ( unionOp | SELECTOP_INTERSECT | SELECTOP_EXCEPT ) + selectStmt )

### Start symbol
sqlQuery = selectStmts + StringEnd()

# Ignore comments
commentStart = Suppress( oneOf('-- #') )
comment = commentStart + restOfLine
sqlQuery.ignore(comment)

################################
# Tests
################################


class TestSqlQueryGrammar(unittest.TestCase):
    PRINT_PARSE_RESULTS = True #bool(os.environ.get('PRINT_PARSE_RESULTS', False))

    """
    Test cases for grammar parsing
    """
    def assertParses(self, inputStr, expectError=False):
        """
        parses :inputStr: and assets the parse succeeded
        (or failed if :expectError: is True)

        returns ParseResults with parse tree

        parameters
        ----------
        inputStr : str
            query string to parse
        expectError : bool
            is this an intentionally malformed inputStr?
            if so, suppresses the ParseException
        """
        if isinstance(inputStr, list):
            return map(lambda i: self.assertParses(i, expectError=expectError), inputStr)

        try:
            if self.PRINT_PARSE_RESULTS and not expectError:
                print
                print inputStr

            tokens = sqlQuery.parseString(inputStr)
            if self.PRINT_PARSE_RESULTS and not expectError:
                print tokens.asXML('query')

            #print tokens.where.dump()

            self.assertFalse(expectError, inputStr) # parsed without error = pass
            return tokens

        except ParseException, err:
            if self.PRINT_PARSE_RESULTS and not expectError:
                #print '%s' % err.line
                print '-' * (err.col - 1) + '^'
                print 'ERROR: %s' % err
            self.assertTrue(expectError, '%s, parsing "%s"' % (err, inputStr))

    @unittest.skip('unimplemented')
    def test_aliases(self):
        pass

    def test_SELECT_with_FROM_and_simple_join(self):
        # valid queries
        results = self.assertParses([

            #'select 1 from a', # unsupported for now

            'select * from xyzzy, ABC',

            'select a, * from xyzzy, ABC',

            'select *, a from xyzzy, ABC',

            'select *, blah from xyzzy , abc',

            'select a,b,c , D ,e from xyzzy,ABC',

            'select all a,b,c from sys.blah ,Table2',

            ])
        self.assertIsNotNone(results)
        for result in results:
            self.assertIsNotNone( result )
            self.assertTrue( len(result.tables) > 1 )
            self.assertTrue( len(result.columns) > 0 )

        # invalid queries
        self.assertParses([

            'select * from a .b'

            ], expectError=True)

    @unittest.skip('unimplemented')
    def test_SELECT_without_FROM(self):
        # standalone 'select x'
        pass

    @unittest.skip('unimplemented')
    def test_PIVOT(self):
        self.assertParses([

            'select a from b pivot ( q for col in (c1, c2, c3) ) where y = 1'

            ])
        pass

    def test_explicit_JOIN(self):
        pass

    def test_WHERE_and_operators(self):
        self.assertParses([

            'select a from b where c = 1',

            'select a from b where c = 1 and d = 2 and e = 3',

            'select a from b where c <=> 1',

            'select a from b where c is null',

            'select a from b where c is not null',

            'select a from b where b.a = "test"',

            'select a from b where c = d or e = "f" or g = 1e2',

            'select a from b where c > 1 and c < 2 and d >= 3 and d <= 4',

            'select a from table where b = 3 and c = -1 or d = 1e-3 or e=-1.2e-3 or f!= -1.2e+3 or g =1.2e3',

            'select a from b where i = 1 or i in (2,3, 4e2 ) and f in( .1, 1.2, -.1, +1.2, +1.2e+3, 1e-1, 1.2e-3, +1.2e-3,-4e2)',

            'SELECT A from sys.blah where a in ("RED","GREEN", "BLUE")',

            'select x from y where z between 10 and 30.5',

            'select distinct a from b,x where ( c = 1 ) or ( d != 2 ) or e >= 3',

            'select a from b where ( c > 1 ) or ( d = 2 ) or e < 3',

            'SeLeCt * fRoM SYS.XYZZY where q is not null and q >= 1e2',

            'select a from b where a not in (1,2,3.5) and d = 1',

            "select distinct A from sys.blah where a in (\"xx\",'yy', 'zz' ) and b in ( 10, 20,30,2.5 )",

            'select a from table where b = 3 and c = -1 and d is null and e is not null',

            'select a from b where c like \'%blah%\' and d not like "%whatever" and c like \'l\'',

            'select x from y,z where y.a != z.a or ( y.a > 3 and y.b = 1 ) and ( y.x <= a.x or ( y.x = 1 or y.y = 3 )) and z in (2,4,6)',

            #'select a from table where b = 3 and c = (select id from d where e = 1)',

            #'select a from b where c in (select d from e where f = 1)',

            ])

    @unittest.skip('unimplemented')
    def test_GROUP_BY(self):
        pass

    @unittest.skip('unimplemented')
    def test_ORDER_BY(self):
        pass

    @unittest.skip('unimplemented')
    def test_HAVING(self):
        pass

    @unittest.skip('unimplemented')
    def test_LIMIT(self):
        pass

    @unittest.skip('unimplemented')
    def test_UNION_and_UNION_ALL(self):
        self.assertParses([

            'select a from b union select c from d',

            'select a from b union all select c from d',

            'select a from b union all (select c from d) except select e from f'

            ])
        pass

    @unittest.skip('unimplemented')
    def test_EXCEPT(self):
        self.assertParses([

            'select a from b except select e from f'

            ])
        pass

    @unittest.skip('unimplemented')
    def test_INTERSECT(self):
        self.assertParses([

            'select a from b intersect select e from f'

            ])
        pass

    def test_comments(self):
        self.assertParses([

            'Select A , b,c from Sys.blah # ignored comment',

            'select A,b from table1,table2 where table1.id = table2.id -- ignored comment'

            ])

if __name__ == '__main__':

    unittest.main()

    # TODO: semantic analysis
    # TODO: dfs walk tokens.where and construct a sqlalchemy Query

