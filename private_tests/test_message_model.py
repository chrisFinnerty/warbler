"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


from app import create_app
import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

# os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

app = create_app('postgresql:///warbler-test', testing=True)


# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
with app.app_context():
    db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            db.drop_all()
            db.create_all()

            self.uid = 94566
            u = User.signup("testing", "testing@test.com", "password", None)
            u.id = self.uid
            db.session.commit()

            self.u = User.query.get(self.uid)

            self.client = app.test_client()

    def tearDown(self):
        with app.app_context():
            res = super().tearDown()
            db.session.rollback()
            return res

    def test_message_model(self):
        """Does basic model work?"""
        with app.app_context():
            m = Message(
                text="a warble",
                user_id=self.uid
            )

            db.session.add(m)
            db.session.commit()

            u = User.query.get(self.uid)

            # User should have 1 message
            self.assertEqual(len(u.messages), 1)
            self.assertEqual(u.messages[0].text, "a warble")

    def test_message_likes(self):
        with app.app_context():
            m1 = Message(
                text="a warble",
                user_id=self.uid
            )

            m2 = Message(
                text="a very interesting warble",
                user_id=self.uid
            )

            u = User.signup("yetanothertest", "t@email.com", "password", None)
            uid = 888
            u.id = uid
            db.session.add_all([m1, m2, u])
            db.session.commit()

            u.likes.append(m1)

            db.session.commit()

            l = Likes.query.filter(Likes.user_id == uid).all()
            self.assertEqual(len(l), 1)
            self.assertEqual(l[0].message_id, m1.id)
