# SqlParse

Parses SQL query into an AST.

This is a custom dialect of SQL. It isn't emulating any particular database server's implementation, but a design
goal is to keep it compatible with ANSI SQL.

## Tests

To run unit tests, run:

    `./setup.py test` or `./sqlparse.py`

## Example

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
