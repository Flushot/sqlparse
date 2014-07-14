import inspect
from abc import ABCMeta, abstractmethod


class QueryBuilder(object):
    """

    """
    _primitives = (int, float, str, unicode, bool)

    def __init__(self, session, model_scope):
        self.session = session
        self.model_scope = model_scope
        self.model_classes = []

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
            return sqlparse.parseString(query_string)
        except pyparsing.ParseException, err:
            msg = [
                'Parse Error: %s' % err,
                query_string,
                '-' * (err.col - 1) + '^',
            ]
            logger.error('\n'.join(msg))
            raise

    def _is_primitive(self, obj):
        return isinstance(obj, self._primitives)

    def _get_model_class(self, class_name):
        klass = self.model_scope[class_name]
        if not inspect.isclass(klass):
            raise ValueError('%s is not a class' % class_name)

        return klass
