import itertools
import logging
import json

import pymongo

from .base import unittest, BuilderTestCase
from sqlparse.builders import MongoQueryBuilder

logger = logging.getLogger(__name__)


class MongoQueryBuilderTest(BuilderTestCase):
    def setUp(self):
        self.client = pymongo.MongoClient('mongodb://localhost:27017')
        self.db = self.client.test

        self.collection = self.db['User']
        self.collection.drop()

        names = {
            'first': [
                'Chris',
                'John',
                'Bob'
            ],
            'last': [
                'Jacob',
                'Smith',
                'Lyon'
            ]
        }

        for idx, (first_name, last_name) in enumerate(itertools.product(names['first'], names['last'])):
            self.collection.insert({
                '_id': str(idx),
                'first_name': first_name,
                'last_name': last_name,
                'is_active': (first_name == 'Chris')
            })

    def tearDown(self):
        self.db = None
        self.client = None

    def test_SELECT(self):
        builder = MongoQueryBuilder(self.db, self.db)
        query, options = builder.parse_and_build("""
            select * from User where
                not (last_name = 'Jacob' or
                    (first_name != 'Chris' and last_name != 'Lyon')) and
                not is_active = 1
            """)

        self.assertEquals('User', builder.model_class)

        #print json.dumps(query, indent=4)
        print json.dumps(query)

        self.assertDictEqual({
            "$and": [
                {
                    "$nor": [
                        {
                            "$or": [
                                {
                                    "last_name": "Jacob"
                                },
                                {
                                    "$and": [
                                        {
                                            "first_name": {
                                                "$ne": "Chris"
                                            }
                                        },
                                        {
                                            "last_name": {
                                                "$ne": "Lyon"
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "$nor": [
                        {
                            "is_active": 1
                        }
                    ]
                }
            ]
        }, query)

        results = self.collection.find(query, options)
        for result in results:
            print json.dumps(result)

        self.assertEquals(4, results.count())
