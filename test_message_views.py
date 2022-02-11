"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, DEFAULT_IMAGE

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ["DATABASE_URL"] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config["WTF_CSRF_ENABLED"] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(
            username="testuser",
            email="test@test.com",
            password="testuser",
            image_url=None,
        )

        self.testuser2 = User.signup(
            username="testuser2",
            email="test2@test.com",
            password="testuser2",
            image_url=None,
        )

        db.session.commit()

        self.testmsg1 = Message(text="yadda yadda", user_id=self.testuser.id)
        self.testmsg2 = Message(text="blahblahblah", user_id=self.testuser2.id)

        db.session.add_all([self.testmsg1, self.testmsg2])
        db.session.commit()

    def test_add_message(self):
        """Can user add a message? Does it show on the homepage,
        user page, and message detail page?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

            response_homepage = c.get("/")
            html_homepage = response_homepage.get_data(as_text=True)

            self.assertIn("Hello</p>", html_homepage)

            response_message_show_page = c.get(f"/messages/{msg.id}")
            html_message_show_page = response_message_show_page.get_data(as_text=True)

            self.assertIn("Hello</p>", html_message_show_page)

            response_user_show_page = c.get(f"/users/{self.testuser.id}")
            html_user_show_page = response_user_show_page.get_data(as_text=True)

            self.assertIn("Hello</p>", html_user_show_page)

    def test_delete_message(self):
        """Can user delete a message? Does it not show on the homepage,
        user page, and message detail page?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "DeleteMePlease"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "DeleteMePlease")

            resp = c.post(f"/messages/{msg.id}/delete")

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            response_homepage = c.get("/")
            html_homepage = response_homepage.get_data(as_text=True)

            self.assertNotIn("DeleteMePlease</p>", html_homepage)

            response_message_show_page = c.get(f"/messages/{msg.id}")
            html_message_show_page = response_message_show_page.get_data(as_text=True)

            self.assertNotIn("DeleteMePlease</p>", html_message_show_page)

            response_user_show_page = c.get(f"/users/{self.testuser.id}")
            html_user_show_page = response_user_show_page.get_data(as_text=True)

            self.assertNotIn("DeleteMePlease</p>", html_user_show_page)

    def test_liking_a_message(self):
        """Can user like a message? Does it show up on the likes page, does the
        like button change on the homepage, user page, and message detail page?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/msg/like/{self.testmsg2.id}")

            self.assertTrue(self.testmsg2.is_liked_by(self.testuser), True)
            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            # response_homepage = c.get("/")
            # html_homepage = response_homepage.get_data(as_text=True)

            # self.assertNotIn("DeleteMePlease</p>", html_homepage)

            # response_message_show_page = c.get(f"/messages/{msg.id}")
            # html_message_show_page = response_message_show_page.get_data(as_text=True)

            # self.assertNotIn("DeleteMePlease</p>", html_message_show_page)

            # response_user_show_page = c.get(f"/users/{self.testuser.id}")
            # html_user_show_page = response_user_show_page.get_data(as_text=True)

            # self.assertNotIn("DeleteMePlease</p>", html_user_show_page)
