try:
    import unittest2 as unittest  # 2.7
except ImportError:
    import unittest  # <2.7
from pyparsing import ParseException
import sqlparse


class BuilderTestCase(unittest.TestCase):
    pass
