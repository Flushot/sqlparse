#!/usr/bin/env python
from pyparsing import Word, White, alphas, nums, alphanums, Literal, CaselessLiteral, \
                        Group, OneOrMore, ZeroOrMore, StringEnd, Forward, Optional, ParseException
import json

# Macros
def delim(literal):
    return Literal(literal).suppress()
def quoted(token):
    return ( apos + token + apos ) | ( quot + token + quot )
def escaped(token):
    return ( backtick + token + backtick ) | token
def commaSeparated(token):
    return ( OneOrMore(token + Literal(',').suppress()) + token ) | token

# Delimiter
eol = delim(';')
apos = delim("'")
quot = delim('"')
backtick = delim('`')
lpar = delim('(')
rpar = delim(')')

relset = escaped(Word(alphas, alphanums))

# todo: include nums, alphas, strings, etc.
integer = Word(nums).setParseAction(lambda s,l,t: int(t[0]))
decimal = Regex(r'^[+-]?\d+(\.\d*)?$').setParseAction(lambda s,l,t: float(t[0]))
number = decimal | integer
string = quoted(Regex('.*'))

atom = number | string

assign = relset + '=' + ( relset | atom )

# select X from X where X group by X having X order by X limit X,X
select = Forward()
proj = relset | atom | Literal('*')
projs = Group(commaSeparated(proj)).setResultsName('projection')
whereClause = CaselessLiteral('where') # incomplete
select << CaselessLiteral('select').setResultsName('statementName') + \
    projs + CaselessLiteral('from') + relset.setResultsName('relsetSource')

# insert into X values (x,x,x)
# insert into X select (x,x,x) ...
# insert delayed into X values (x,x,x)
# insert into X (x,x,x) select (x,x,x) ...
# insert into X (x,x,x) values (x,x,x)
# insert into X (x,x,x) values (x,x,x), (x,x,x)
# insert high_priority into X values (x,x,x) on duplicate key update x=x,x=x
insertCols = lpar + commaSeparated(relset) + rpar
insertVals = lpar + Group(commaSeparated(relset | atom)) + rpar
insertLockOption = Optional(CaselessLiteral('low_priority') | CaselessLiteral('delayed') | CaselessLiteral('high_priority')).setResultsName('lockOption')
insert = CaselessLiteral('insert').setResultsName('statementName') + \
    insertLockOption + Optional(CaselessLiteral('ignore').setParseAction(lambda s,l,t: True).setResultsName('ignoreOption')) + \
    CaselessLiteral('into').suppress() + relset.setResultsName('relsetTarget') + \
    insertCols.setResultsName('insertColumns') + \
    ( select | (CaselessLiteral('values') + \
        Group((commaSeparated(insertVals) | insertVals)).setResultsName('insertValues') ) ) + \
    Optional(CaselessLiteral('on duplicate key update')) # col_name=expr, ...

statement = Optional(White().suppress()) + ( select | insert ) #| assign

sql = OneOrMore(statement + eol) | ( statement + Optional(eol) )

if __name__ == '__main__':
    #
    # test cases
    #
    for query in [
            "select * from table",

            "select a, b, 1 from table",

            "insert into table (x) values (y)",

            "insert into tableA (a, `b`, c) select d, `e`, 1 from tableB",

            """
            insert 
            into table(a, b,c)
            values 
            (d,e, f)
            """,

            "insert into `table` (a, b) values ('c', 2)",

            "insert into table (a,b) values(1,2),(3, 4), (5, 6)",

            "insert low_priority into table (a,b) values (1,2);"

            """
            insert into table (a, b) values ('c', 'd');
            insert into `table`(e,f) values(g,h)
            """
        ]:
        print query
        try:
            toks = sql.parseString(query)
            if toks.statementName == 'insert':
                records = [ dict(zip(toks.insertColumns, valTuple)) for valTuple in toks.insertValues ]
                print json.dumps(records, indent=4)
            else:
                print toks
            print 'PASS'
        except ParseException, err:
            print 'FAIL : Syntax error in: "%s"' % err.line
            print '                         ' + '-'*(err.col-1) + '^ %s' % err # ---^ pointer
        print '='*80
