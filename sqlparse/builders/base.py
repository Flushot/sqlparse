import inspect
import logging
from abc import ABCMeta, abstractmethod

import sqlparse
import pyparsing

logger = logging.getLogger(__name__)


class QueryBuilder(object):
    """

    """
    _primitives = (int, float, str, unicode, bool)

    def __init__(self):
        self.model_class = None  # deprecated
        self.model_classes = []
        self.fields = []

    @abstractmethod
    def parse_and_build(self, query_string):
        pass

    def _parse(self, query_string):
        try:
            ast = sqlparse.parse_string(query_string)
        except pyparsing.ParseException, err:
            msg = [
                'Parse Error: %s' % err,
                query_string,
                '-' * (err.col - 1) + '^',
            ]
            logger.error('\n'.join(msg))
            raise

        return ast
