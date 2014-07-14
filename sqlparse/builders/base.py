import inspect
from abc import ABCMeta, abstractmethod


class QueryBuilder(object):
    """

    """
    _primitives = (int, float, str, unicode, bool)

    def __init__(self, session, model_scope):
        self.session = session
        self.model_scope = model_scope

    @abstractmethod
    def parse_and_build(self, query_string):
        """

        :param query_string:
        :return:
        """
        pass

    def _is_primitive(self, obj):
        return isinstance(obj, self._primitives)

    def _get_model_class(self, className):
        klass = self.model_scope[className]
        if not inspect.isclass(klass):
            raise ValueError('%s is not a class' % className)
        return klass
