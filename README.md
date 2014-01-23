# SqlParse

This is a DBMS-agnostic SQL grammar that should be compatible with ANSI SQL, but has some language extensions
for things I've found useful (such as T-SQL's PIVOT). Feel free to use this as a template for extending the
SQL language.

# Ideas

I'd like to eventually add graph traversal constructs to the language (using Gremlin as an influence).
This will be useful in hybrid relational-graph databases.

# Tests

Just run `sqlparse.py` to ensure the grammar is working with your version of Python. It will run all the pyunit tests.

# Example

    import sql_grammar

    parse_tree = sql_grammar.parse('select * from whatever where a = 1')
    print parse_tree.asXML('query')

