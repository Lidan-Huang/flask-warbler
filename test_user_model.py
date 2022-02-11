"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


from app import app
import os
from unittest import TestCase

from models import db, User, Message, Follows, DEFAULT_IMAGE

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


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.u = User(
            email="test@test.com", username="testuser", password="HASHED_PASSWORD"
        )

        self.u2 = User(
            email="test2@test.com", username="testuser2", password="HASHED_PASSWORD"
        )

        db.session.add_all([self.u, self.u2])
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        # User should have no messages & no followers
        self.assertEqual(len(self.u.messages), 0)
        self.assertEqual(len(self.u.followers), 0)
        self.assertEqual(repr(self.u), f"<User #{self.u.id}: testuser, test@test.com>")

    def test_following(self):
        self.u.following.append(self.u2)
        db.session.commit()
        self.assertTrue(self.u.is_following(self.u2), True)
        self.assertTrue(self.u2.is_followed_by(self.u), True)

        self.u.following.remove(self.u2)
        db.session.commit()
        self.assertFalse(self.u.is_following(self.u2), True)
        self.assertFalse(self.u2.is_followed_by(self.u), True)

    def test_signup(self):
        u3 = User(
            email="user3@test.com",
            username="testuser_03",
            password="HASHED_PASSWORD",
            image_url=DEFAULT_IMAGE,
        )

        response = User.signup(u3.username, u3.email, u3.password, u3.image_url)
        db.session.commit()
        user = User.query.filter(User.username == u3.username).one()

        self.assertNotEqual(response, False)
        self.assertEqual(len(User.query.all()), 3)
        self.assertEqual(user.email, "user3@test.com")
        self.assertEqual(user.image_url, DEFAULT_IMAGE)

    def test_signup_failure(self):
        bad_user = User(
            email="badboy@breakyourapp.com", username=1212, password="", image_url=""
        )
        response = ""
        try:
            response = User.signup(
                bad_user.email, bad_user.username, bad_user.password, bad_user.image_url
            )
            db.session.commit()
        except:
            print("error happened")

        self.assertFalse(response, True)
        self.assertEqual(len(User.query.all()), 2)
