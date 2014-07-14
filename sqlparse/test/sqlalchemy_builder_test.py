import itertools
import logging

import sqlalchemy.orm
import sqlalchemy.ext.declarative

from .base import BuilderTestCase
from sqlparse.builders import SqlAlchemyQueryBuilder

logger = logging.getLogger(__name__)


class SqlAlchemyQueryBuilderTest(BuilderTestCase):
    def setUp(self):
        self.engine = sqlalchemy.create_engine('sqlite://', echo=False)

        Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session = Session()

        Base = sqlalchemy.ext.declarative.declarative_base(bind=self.engine)

        class User(Base):
            __tablename__ = 'users'

            id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
            first_name = sqlalchemy.Column(sqlalchemy.String)
            last_name = sqlalchemy.Column(sqlalchemy.String)
            is_active = sqlalchemy.Column(sqlalchemy.Boolean)

            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

            def __str__(self):
                return '%s %s' % (self.first_name, self.last_name)

        self.User = User
        self.model_scope = dict(User=self.User)

        # Add seed data
        Base.metadata.create_all()

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
        for first_name, last_name in itertools.product(names['first'], names['last']):
            self.session.add(User(
                first_name=first_name,
                last_name=last_name,
                is_active=(first_name == 'Chris')))

        self.session.commit()

    def tearDown(self):
        pass

    def test_SELECT(self):
        builder = SqlAlchemyQueryBuilder(self.session, self.model_scope)
        query = builder.parse_and_build("""
            select * from User where
                not (last_name = 'Jacob' or
                    (first_name != 'Chris' and last_name != 'Lyon')) and
                not is_active = 1
            """)

        results = query.all()
        #for user in results:
        #    logger.info(user)

        self.assertEquals(4, len(results))
