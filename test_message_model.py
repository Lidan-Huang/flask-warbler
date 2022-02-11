"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


from app import app
import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes, DEFAULT_IMAGE

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ["DATABASE_URL"] = "postgresql:///warbler_test"

# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.u = User.signup(
            "testuser", "test@test.com", "HASHED_PASSWORD", DEFAULT_IMAGE
        )
        self.u2 = User.signup(
            "testuser2", "test2@test.com", "HASHED_PASSWORD", DEFAULT_IMAGE
        )
        db.session.commit()

        self.m1 = Message(text="I am a super neat test message!", user_id=self.u.id)
        self.m2 = Message(text="I am another test message :)", user_id=self.u.id)

        db.session.add_all([self.m1, self.m2])
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_message_model(self):
        """Does basic model work?"""

        # User should have no messages & no followers
        self.assertEqual(len(self.m1.text), 31)
        self.assertEqual(self.m1.user_id, self.u.id)

    def test_create_message(self):
        "Can we successfully create a new message?"

        new_message = Message(text="hello, I'm message 3", user_id=self.u.id)

        db.session.add(new_message)
        db.session.commit()

        check_new_message = Message.query.get(new_message.id)
        self.assertEqual(len(check_new_message.text), 20)
        self.assertEqual(len(self.u.messages), 3)

    def test_like_message(self):
        "Can user2 like the first message from user 1?"

        new_like = Likes(user_id=self.u2.id, message_being_liked_id=self.m1.id)

        db.session.add(new_like)
        db.session.commit()

        self.assertTrue(self.u2.is_liking(self.m1), True)
        self.assertTrue(self.m1.is_liked_by(self.u2), True)
