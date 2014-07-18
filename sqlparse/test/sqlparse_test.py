from .base import ParserTestCase, unittest

class TestSqlQueryGrammar(ParserTestCase):
    """
    Test cases for grammar parsing
    """
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
            self.assertTrue( len(result.tables.values) > 1 )
            self.assertTrue( len(result.columns.values) > 0 )

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

            'select a from b where c like \'%%blah%%\' and d not like "%%whatever" and c like \'l\'',

            'select x from y,z where y.a != z.a or ( y.a > 3 and y.b = 1 ) and ( y.x <= a.x or ( y.x = 1 or y.y = 3 )) and z in (2,4,6)',

            ])

    @unittest.skip('unimplemented')
    def test_subselect(self):
        self.assertParses([

            'select a from table where b = 3 and c = (select id from d where e = 1)',

            'select a from b where c in (select d from e where f = 1)',

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

    @unittest.skip('unimplemented')
    def test_EXCEPT(self):
        self.assertParses([

            'select a from b except select e from f'

            ])

    @unittest.skip('unimplemented')
    def test_INTERSECT(self):
        self.assertParses([

            'select a from b intersect select e from f'

            ])

    def test_comments(self):
        self.assertParses([

            'Select A , b,c from Sys.blah # ignored comment',

            'select A,b from table1,table2 where table1.id = table2.id -- ignored comment'

            ])

if __name__ == '__main__':
    #import operator
    #import sqlalchemy

    unittest.main()

    # TODO: semantic analysis
    # TODO: dfs walk tokens.where and construct a sqlalchemy Query

