"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

# os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import create_app

app = create_app('postgresql:///warbler-test', testing=True)

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
with app.app_context():
    db.drop_all()
    db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            db.create_all()

            self.client = app.test_client()

    def tearDown(self):
        """Tear down after each test."""

        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        with app.app_context():
            db.session.add(u)
            db.session.commit()

        # User should have no messages & no followers

            self.assertEqual(len(u.messages), 0)
            self.assertEqual(len(u.followers), 0)

    def test_repr(self):
        """Testing if __repr__ method on User model works."""

        u = User(email='test2@email.com', username='testuser2', password='password')

        with app.app_context():
            db.session.add(u)
            db.session.commit()

            fetched_user = User.query.filter_by(email='test2@email.com').first()
            self.assertEqual(repr(fetched_user), f'<User #{fetched_user.id}: {fetched_user.username}, {fetched_user.email}>')

    def test_is_following_true_false(self):
        """Tests if is_following detects when u1 is following u2"""

        u1 = User(
            email="test@xyz.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test@cnn.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        with app.app_context():
            db.session.add_all([u1, u2])
            db.session.commit()

            follow = Follows(user_being_followed_id=u2.id, user_following_id=u1.id)
            db.session.add(follow)
            db.session.commit()

            # is_following tests
            self.assertTrue(u1.is_following(u2))
            self.assertFalse(u2.is_following(u1))

            # is_followed_by tests
            self.assertTrue(u2.is_followed_by(u1))
            self.assertFalse(u1.is_followed_by(u2))

    def test_user_signup(self):
        """Tests if user.signup successfully creates a new user."""

        u = User(
            email = 'newuser123@email.com',
            username='testnewuser123',
            password='NEWPASSWORD',
            image_url='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQlzjNjOtynI8ZbZyob2MfPHnrTFHgtb63uUw&s'
        )
        
        with app.app_context():
            signup = u.signup(username=u.username, email=u.email, password=u.password, image_url=u.image_url)
            db.session.add(signup)
            db.session.commit()

            self.assertTrue(signup.id)

    def test_user_auth(self):
        """Tests if user.signup successfully creates a new user."""

        u = User(
            email = 'newuser123@email.com',
            username='testnewuser123',
            password='NEWPASSWORD',
            image_url='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQlzjNjOtynI8ZbZyob2MfPHnrTFHgtb63uUw&s'
        )
        
        with app.app_context():
            signup = u.signup(username=u.username, email=u.email, password=u.password, image_url=u.image_url)
            db.session.add(signup)
            db.session.commit()

            auth_user = u.authenticate(username=u.username, password=u.password)
            # checks if authenticated user id matches the signed up user
            self.assertEqual(auth_user.id, signup.id)


