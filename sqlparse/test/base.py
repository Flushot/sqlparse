import os
import unittest

from pyparsing import ParseException
import sqlparse


class BuilderTestCase(unittest.TestCase):
    pass


class ParserTestCase(unittest.TestCase):
    # Print results XML to console?
    PRINT_PARSE_RESULTS = bool(os.environ.get('PRINT_PARSE_RESULTS', False))

    def assertParses(self, input_str: str, expect_error: bool = False):
        """
        parses :input_str: and assets the parse succeeded
        (or failed if :expectError: is True)

        returns ParseResults with parse tree

        parameters
        ----------
        input_str : str
            query string to parse
        expect_error : bool
            is this an intentionally malformed inputStr?
            if so, suppresses the ParseException
        """
        if isinstance(input_str, list):
            return map(lambda i: self.assertParses(i, expect_error=expect_error), input_str)

        try:
            if self.PRINT_PARSE_RESULTS and not expect_error:
                print("\n{}".format(input_str))

            tokens = sqlparse.parse_string(input_str)
            if self.PRINT_PARSE_RESULTS and not expect_error:
                print(tokens.asXML('query'))
                #print tokens.where.dump()

            #print tokens.where.dump()

            self.assertFalse(expect_error, input_str) # parsed without error = pass
            return tokens

        except ParseException as err:
            if self.PRINT_PARSE_RESULTS and not expect_error:
                # print(err.line)
                print('-' * (err.col - 1) + '^')
                print('ERROR: {}'.format(err))
            self.assertTrue(expect_error, '{}, parsing "{}"'.format(err, input_str))
