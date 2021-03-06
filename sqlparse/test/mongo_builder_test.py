import itertools
import logging

import pymongo

from .base import BuilderTestCase
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
        builder = MongoQueryBuilder()
        query, options = builder.parse_and_build("""
            select a,b from User where
                not ( last_name= 'Jacob' or
                      (first_name !='Chris' and last_name!='Lyon') ) and
                not is_active = 1
            """)

        self.assertEquals('User', builder.model_class)

        self.assertEquals(['a', 'b'], builder.fields)
        self.assertDictEqual({
            'fields': {
                'a': 1,
                'b': 1
            }
        }, options)

        self.assertDictEqual({
            "$and": [
                {
                    "$nor": [
                        {
                            "$or": [
                                { "last_name": "Jacob" },
                                {
                                    "$and": [
                                        {"first_name": {"$ne": "Chris"}},
                                        {"last_name": {"$ne": "Lyon"}}
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "$nor": [
                        {"is_active": 1}
                    ]
                }
            ]
        }, query)

        results = self.collection.find(query, options)
        # for result in results:
        #     print(json.dumps(result))

        self.assertEquals(4, results.count())
