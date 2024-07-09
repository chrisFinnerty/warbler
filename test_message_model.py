"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from datetime import datetime

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import create_app

app = create_app('warbler-test', testing=True)

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
with app.app_context():
    db.drop_all()
    db.create_all()


class MessageModelTestCase(TestCase):
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

    def test_message_model(self):
        """Does basic msg model work?"""

        u = User(
            username='testthisout',
            email='testesttest123@email.com',
            password='password'
        )


        with app.app_context():
            db.session.add(u)
            db.session.commit()

            message = Message(
                text='THIS IS A TEST!',
                timestamp='07 07 2024',
                user_id=u.id
            )

            db.session.add(message)
            db.session.commit()

            # checks if the message is added to the user model successfully
            self.assertEqual(len(u.messages), 1)
            # checks if the message was in fact created in the db
            self.assertEqual(message.id, 1)

    def test_message_delete_cascase(self):
        """When a user is deleted, does this in turn also delete any message(s) tied to that user?"""

        u = User(
            username='testthisout',
            email='testesttest123@email.com',
            password='password'
        )
    
        with app.app_context():
            db.session.add(u)
            db.session.commit()

            message1 = Message(
                text='THIS IS A TEST!',
                timestamp='07 07 2024',
                user_id=u.id
            )

            message2 = Message(
                text='THIS IS A TEST!',
                timestamp='07 07 2024',
                user_id=u.id
            )

            db.session.add_all([message1, message2])

            db.session.delete(u)
            db.session.commit()

            message_count = Message.query.filter_by(user_id=u.id).count()
            self.assertEqual(message_count, 0)

    def test_unauthenticated_user_message_permission(self):
        """Users that are not logged in should not have the ability to create a message."""

        response = self.client.post('/messages/new', data=dict(
            text='Test Message'
        ), follow_redirects=True)
        
        with app.app_context():
            created_message = Message.query.filter_by(text='Test message').first()

        self.assertIsNone(created_message)

    def test_message_text_limit(self):
        u = User(
            username='testthisout',
            email='testesttest123@email.com',
            password='password'
        )

        with app.app_context():
            db.session.add(u)
            db.session.commit()

            message = Message(
                text='Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu. In enim justo, rhoncus ut, imperdiet a, venenatis vitae, justo. Nullam dictum felis eu pede mollis pretium. Integer tincidunt. Cras dapibus. Vivamus elementum semper nisi. Aenean vulputate eleifend tellus. Aenean leo ligula, porttitor eu, consequat vitae, eleifend ac, enim. Aliquam lorem ante, dapibus in, viverra quis, feugiat a, tellus. Phasellus viverra nulla ut metus varius laoreet. Quisque rutrum. Aenean imperdiet. Etiam ultricies nisi vel augue. Curabitur ullamcorper ultricies nisi. Nam eget dui. Etiam rhoncus. Maecenas tempus, tellus eget condimentum rhoncus, sem quam semper libero, sit amet adipiscing sem neque sed ipsum. Nam quam nunc, blandit vel, luctus pulvinar, hendrerit id, lorem. Maecenas nec odio et ante tincidunt tempus. Donec vitae sapien ut libero venenatis faucibus. Nullam quis ante. Etiam sit amet orci eget eros faucibus tincidunt. Duis leo. Sed fringilla mauris sit amet nibh. Donec sodales sagittis magna. Sed consequat, leo eget bibendum sodales, augue velit cursus nunc',
                timestamp=datetime.utcnow(),
                user_id=u.id
            )

        with self.assertRaises(Exception):
            with app.app_context():
                db.session.add(message)
                db.session.commit()

        with app.app_context():
            created_message = Message.query.filter_by(user_id=u.id).first()
            self.assertIsNone(created_message)

    