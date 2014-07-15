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

    def __init__(self, session, model_scope):
        self.session = session
        self.model_scope = model_scope
        #self.model_classes = []

    @abstractmethod
    def parse_and_build(self, query_string):
        """

        :param query_string:
        :return:
        """
        pass

    def _parse(self, query_string):
        try:
            #logger.debug('Parsing: %s' % queryString)
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

    def _is_primitive(self, obj):
        return isinstance(obj, self._primitives)
