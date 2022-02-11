"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


from app import app
import os
from unittest import TestCase

from models import db, User, Message, Follows

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

        self.u = User.signup("testuser", "test@test.com", "HASHED_PASSWORD", DEFAULT_IMAGE)
        self.u2 = User.signup("testuser2", "test2@test.com", "HASHED_PASSWORD", DEFAULT_IMAGE)
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_message_model(self):
        """Does basic model work?"""

        # User should have no messages & no followers
        self.assertEqual(len(self.u.messages), 0)
        self.assertEqual(len(self.u.followers), 0)
        self.assertEqual(repr(self.u), f"<User #{self.u.id}: testuser, test@test.com>")

   