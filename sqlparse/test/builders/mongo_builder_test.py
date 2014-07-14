import itertools
import logging

import pymongo

from .base import unittest, BuilderTestCase
from sqlparse.builders import MongoQueryBuilder

logger = logging.getLogger(__name__)


class MongoQueryBuilderTest(BuilderTestCase):
    def setUp(self):
        # TODO: set up seed data
        pass

    def tearDown(self):
        pass

    @unittest.skip('not implemented')
    def test_SELECT(self):
        builder = MongoQueryBuilder(self.session, self.model_scope)
        query = builder.parse_and_build("""
            select * from User where
                not (last_name = 'Jacob' or
                    (first_name != 'Chris' and last_name != 'Lyon')) and
                not is_active = 1
            """)
        for user in query.all():
            logger.info(user)

        self.assertTrue(False)
