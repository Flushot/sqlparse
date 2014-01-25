# SqlParse

This is a DBMS-agnostic SQL grammar that should be compatible with ANSI SQL, but has some language extensions
for things I've found useful (such as T-SQL's PIVOT). Intent is to use this as a template for extending the
SQL language.

# Tests

To run unit tests, either run `./setup.py test` or `./sqlparse.py`

# Example

    import sqlparse

    parse_tree = sqlparse.sqlQuery.parseString('select * from whatever where a = 1')
    print parse_tree.asXML('query')
