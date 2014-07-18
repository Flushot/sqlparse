from . import builders, nodes, visitors, grammar


__version__ = '0.2.0'

__all__ = [
    'builders',
    'nodes',
    'visitors',
    'parse_string'
]


def parse_string(query_string):
    """
    Parses :query_string: into an AST
    """
    return grammar.sqlQuery.parseString(query_string)
