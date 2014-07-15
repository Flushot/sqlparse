# SqlParse

Parses and transforms SQL queries.

This project started as an experiement in writing parsers, and still remains that way.
It's incomplete, so please don't use it in production code.

## What's supported already?

* Parser
    * Grammar: SELECT ... FROM ... [ WHERE ... ] [ ORDER BY ... ]
    * Where clause expression tree
    * Source tables/models (in FROM)
    * Projections

* Query builder
    * Transform SQL into Mongo queries
    * Transform SQL into SqlAlchemy queries

## Roadmap

Here's a list of features that are currently in the plans for development:

* Grammar
    * Aliases
    * Joins
    * Unions
    * Pivots
    * Functions
    * Bitwise operators
    * Math expressions
    * GROUP BY and HAVING
    * LIMIT and OFFSET
    * EXCEPT and INTERSECT

* Parser
    * Null-safe equality
    * Type checking
    * Logical optimizations
    * Multiple tables/models

* General
    * Better test coverage

## Tests

<a href="https://travis-ci.org/Flushot/sqlparse/builds"><img src="https://travis-ci.org/Flushot/sqlparse.svg" data-bindattr-25="25" title="Build Status Images" border="0"></a>

To run unit tests:

`./setup.py test` or `make test`

## Examples

Parsing SQL query into a <a href="https://pythonhosted.org/pyparsing/pyparsing.pyparsing.ParseResults-class.html">pyparsing</a> parse tree:

    >>> ast = sqlparse.parseString('select a from b where c = 1 and d = 2 or e = "f"')
    >>> print ast.asXML('query')
    <query>
      <columns>
        <column>a</column>
      </columns>
      <tables>
        <table>b</table>
      </tables>
      <where>(and (= c 1) (or (= d 2) (= e "f")))</where>
    </query>
    >>> print ast.tables.asXML('tables')
    <tables>
      <table>b</table>
    </tables>    

Building a SqlAlchemy query object from a parsed SQL query:

    >>> builder = sqlparse.bulders.SqlAlchemyQueryBuilder(sa_session, globals())
    >>> sqlalchemy_query = builder.parse_and_build("""
    ...     select * from User where
    ...         not (last_name = 'Jacob' or
    ...             (first_name != 'Chris' and last_name != 'Lyon')) and
    ...         not is_active = 1
    ... """)
    >>> for result in sqlalchemy_query.all():
    ...     # do something

Building a MongoDB query object from a parsed SQL query:

    >>> builder = sqlparse.builders.MongoQueryBuilder(pymongo_database)
    >>> mongo_query = builder.parse_and_build("""
    ...     select * from User where
    ...         not (last_name = 'Jacob' or
    ...             (first_name != 'Chris' and last_name != 'Lyon')) and
    ...         not is_active = 1
    ... """)
    >>> print json.dumps(mongo_query, indent=4)
    {
        "$and": [
            {
                "$nor": [
                    {
                        "$or": [
                            {
                                "last_name": "Jacob"
                            },
                            {
                                "$and": [
                                    {
                                        "first_name": {
                                            "$ne": "Chris"
                                        }
                                    },
                                    {
                                        "last_name": {
                                            "$ne": "Lyon"
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "$nor": [
                    {
                        "is_active": 1
                    }
                ]
            }
        ]
    }


## License

    Copyright 2014 Chris Lyon
    
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
    
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
