"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


from app import create_app, CURR_USER_KEY
import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

# os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

app = create_app('postgresql:///warbler-test', testing=True)

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
with app.app_context():
    db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            db.drop_all()
            db.create_all()

            self.client = app.test_client()

            self.testuser = User.signup(username="testuser",
                                        email="test@test.com",
                                        password="testuser",
                                        image_url=None)
            db.session.commit()
            self.testuser_id = self.testuser.id

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_add_message(self):
        """Can user add a message?"""
        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser_id

                resp = c.post("/messages/new", data={"text": "Hello"})

                # Make sure it redirects
                self.assertEqual(resp.status_code, 302)

                msg = Message.query.one()
                self.assertEqual(msg.text, "Hello")

    def test_add_no_session(self):
        with self.client as c:
            resp = c.post("/messages/new",
                          data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_add_invalid_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 99222224  # user does not exist

            resp = c.post("/messages/new",
                          data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_message_show(self):
        with app.app_context():

            m = Message(
                id=1234,
                text="a test message",
                user_id=self.testuser_id
            )
            db.session.add(m)
            db.session.commit()

            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id

                m = Message.query.get(1234)

                resp = c.get(f'/messages/{m.id}')

                self.assertEqual(resp.status_code, 200)
                self.assertIn(m.text, str(resp.data))

    def test_invalid_message_show(self):
        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser_id

                resp = c.get('/messages/99999999')

                self.assertEqual(resp.status_code, 404)

    def test_message_delete(self):
        with app.app_context():
            m = Message(
                id=1234,
                text="a test message",
                user_id=self.testuser_id
            )

            db.session.add(m)
            db.session.commit()

            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id

                resp = c.post("/messages/1234/delete", follow_redirects=True)
                self.assertEqual(resp.status_code, 200)

                m = Message.query.get(1234)
                self.assertIsNone(m)

    def test_unauthorized_message_delete(self):
        with app.app_context():
            # A second user that will try to delete the message
            u = User.signup(username="unauthorized-user",
                            email="testtest@test.com",
                            password="password",
                            image_url=None)
            db.session.commit()
            unauthorized_user_id = u.id

            # Message is owned by testuser
            m = Message(
                id=1234,
                text="a test message",
                user_id=self.testuser_id
            )
            db.session.add(m)
            db.session.commit()

            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = unauthorized_user_id

                resp = c.post("/messages/1234/delete", follow_redirects=True)
                self.assertEqual(resp.status_code, 200)
                self.assertIn("Access unauthorized", str(resp.data))

                m = Message.query.get(1234)
                self.assertIsNotNone(m)

    def test_message_delete_no_authentication(self):

        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser_id
        )
        with app.app_context():
            db.session.add(m)
            db.session.commit()

        with self.client as c:
            resp = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            m = Message.query.get(1234)
            self.assertIsNotNone(m)
