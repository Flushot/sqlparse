import os
import sys
import collections
try:
    import unittest2 as unittest  # 2.7
except ImportError:
    import unittest  # <2.7
from pyparsing import ParseException
import sqlparse


class BuilderTestCase(unittest.TestCase):
    pass


class ParserTestCase(unittest.TestCase):
    # Print results XML to console?
    PRINT_PARSE_RESULTS = bool(os.environ.get('PRINT_PARSE_RESULTS', False))

    def assertParses(self, inputStr, expectError=False):
        """
        parses :inputStr: and assets the parse succeeded
        (or failed if :expectError: is True)

        returns ParseResults with parse tree

        parameters
        ----------
        inputStr : str
            query string to parse
        expectError : bool
            is this an intentionally malformed inputStr?
            if so, suppresses the ParseException
        """
        if isinstance(inputStr, list):
            return map(lambda i: self.assertParses(i, expectError=expectError), inputStr)

        try:
            if self.PRINT_PARSE_RESULTS and not expectError:
                print
                print inputStr

            tokens = sqlparse.parse_string(inputStr)
            if self.PRINT_PARSE_RESULTS and not expectError:
                print tokens.asXML('query')
                #print tokens.where.dump()

            #print tokens.where.dump()

            self.assertFalse(expectError, inputStr) # parsed without error = pass
            return tokens

        except ParseException, err:
            if self.PRINT_PARSE_RESULTS and not expectError:
                #print '%s' % err.line
                print '-' * (err.col - 1) + '^'
                print 'ERROR: %s' % err
            self.assertTrue(expectError, '%s, parsing "%s"' % (err, inputStr))


