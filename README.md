# SqlParse

Parses SQL query into an AST.

This is a custom dialect of SQL. It isn't emulating any particular database server's implementation, but a design
goal is to keep it compatible with ANSI SQL.

## Tests

To run unit tests, run:

    `./setup.py test` or `./sqlparse.py`

## Example

    import sqlparse

    parse_tree = sqlparse.sqlQuery.parseString('select * from whatever where a = 1')
    print parse_tree.asXML('query')

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
