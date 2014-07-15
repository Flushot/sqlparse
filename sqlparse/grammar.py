#!/usr/bin/env python
#
# Copyright 2014 Chris Lyon <flushot@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import pyparsing
from pyparsing import \
    Forward, Group, Combine, Suppress, StringEnd, \
    Optional, ZeroOrMore, OneOrMore, oneOf, \
    operatorPrecedence, opAssoc, \
    Word, Literal, CaselessLiteral, Regex, \
    alphas, nums, alphanums, quotedString, \
    restOfLine, quotedString, delimitedList, \
    ParseResults, ParseException

from .opers import *

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
OP_EQUAL = Literal('=')
OP_VAL_NULLSAFE_EQUAL = Literal('<=>')
OP_NOTEQUAL = ( Literal('!=') | Literal('<>') )
OP_GT = Literal('>').setName('gt')
OP_LT = Literal('<').setName('lt')
OP_GTE = Literal('>=').setName('ge')
OP_LTE = Literal('<=').setName('le')
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
LOGOP_AND = ( CaselessLiteral('and') | CaselessLiteral('&&') )
LOGOP_OR =  ( CaselessLiteral('or')  | CaselessLiteral('||') )
LOGOP_NOT = ( CaselessLiteral('not') | CaselessLiteral('!')  )
LOGOP_XOR = CaselessLiteral('xor')

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
inOperand = Suppress(L_PAREN) + Group(delimitedList(columnRval))('value').setParseAction(ListValue) + Suppress(R_PAREN)
# TODO: Functions: sum, avg, count, max, min, ifnull/isnull, if
#            current_date, current_time, current_timestamp, current_user
#            substring, regex, concat, group_concat
#            cast, convert
whereCond = Forward()
whereCond << (
    Group(LOGOP_NOT + whereCond)('op').setParseAction(UnaryOperator) |
    Group( columnName('column') + equalityOp('op') + columnRval ).setParseAction(BinaryOperator) |  # x = y, x != y, etc.
    Group( columnName('column') + likeOp('op') + likePattern ).setParseAction(BinaryOperator) |
    Group( columnName('column') + betweenOp('op') + Group( columnRval + OP_BETWEEN_AND + columnRval )('range').setParseAction(RangeValue) ).setParseAction(BinaryOperator) |  # x between y and z, x not between y and z
    Group( columnName('column') + Group( OP_IS + Optional(LOGOP_NOT) )('op') + ( VAL_NULL | VAL_TRUE | VAL_FALSE | VAL_UNKNOWN )('value') ) |  # x is null, x is not null
    Group( columnName('column') + OP_IN('op') + inOperand ).setParseAction(BinaryOperator) |
    #Group( columnName('column') + Combine( LOGOP_NOT + OP_IN )('op') + inOperand ) |
    ( L_PAREN + whereExpr('expr') + R_PAREN )
    )


# logOp = operatorPrecedence(
#     whereExpr('expr'), [
#         (LOGOP_NOT, 1, opAssoc.RIGHT, UnaryOperator),
#         (LOGOP_AND, 2, opAssoc.RIGHT, BinaryOperator),
#         (LOGOP_OR,  2, opAssoc.RIGHT, BinaryOperator)
#     ])
whereExpr << (
    whereCond ^
    #Group( LOGOP_NOT('op') + whereCond )('expr').setParseAction(UnaryOperator) ^
    Group(
        whereCond +
        OneOrMore(
            LOGOP_AND('op') + whereExpr('expr') |
            LOGOP_XOR('op') + whereExpr('expr') |
            LOGOP_OR('op') + whereExpr('expr')
        )
    ).setParseAction(BinaryOperator)
    )

columnProjection = (
    Optional( SELECT_DISTINCT | SELECT_ALL ).setResultsName('options') +
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
# TODO: LIMIT, OFFSET

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
