# SqlParse

Parses and transforms SQL queries.

This is a custom dialect of SQL for experimentation purposes. It isn't emulating any particular database server's implementation, but a design goal is to keep it compatible with ANSI SQL.

## Tests

<a href="https://travis-ci.org/Flushot/sqlparse/builds"><img src="https://travis-ci.org/Flushot/sqlparse.svg" data-bindattr-25="25" title="Build Status Images" border="0"></a>

To run unit tests, run:

    `./setup.py test` or `./sqlparse.py`

## Examples

Parsing SQL query into an abstract syntax tree:

    >>> import sqlparse
    >>> ast = sqlparse.sqlQuery.parseString('select a from b where c = 1 and d = 2 or e = "f"')
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

Converting a SQL query into a SqlAlchemy query:

    >>> import sqlparse
    >>> builder = SqlAlchemyQueryBuilder(sa_session, globals())
    >>> sqlalchemy_query = builder.parse_and_build("""
    ...     select * from User where
    ...         not (last_name = 'Jacob' or
    ...             (first_name != 'Chris' and last_name != 'Lyon')) and
    ...         not is_active = 1
    ... """)
    >>> for result in sqlalchemy_query.all():
    ...     # do something

Converting a SQL query into a MongoDB query:

    >>> import sqlparse, json
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
