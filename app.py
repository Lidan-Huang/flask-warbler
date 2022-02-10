import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

from forms import CSRFProtectForm, UserAddForm, LoginForm, MessageForm, UserEditForm
from models import db, connect_db, User, Message

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"].replace(
    "postgres://", "postgresql://"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = False
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = True
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# ~~ User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


@app.before_request
def add_csrf_keys_to_g():
    """If we're logged in, add the WTF CSRF token to the Flask global"""

    # g.logout_form = CSRFProtectForm()
    # g.delete_form = CSRFProtectForm()
    g.csrf_checking = CSRFProtectForm()


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", "danger")
            return render_template("users/signup.html", form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template("users/signup.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", "danger")

    return render_template("users/login.html", form=form)


@app.post("/logout")
def logout():
    """Handle logout of user."""

    # IMPLEMENT THIS AND FIX BUG
    # DO NOT CHANGE METHOD ON ROUTE

    if not g.user:
        flash("access unauthorized", "danger")
        return redirect("/")
    if g.csrf_checking.validate_on_submit():
        do_logout()
        flash("You have been sucessfully logout!")
        return redirect("/")
    else:
        flash("access unauthorized", "danger")
        return redirect("/")


##############################################################################
# ~~ General user routes:


@app.get("/users")
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """
    search = request.args.get("q")

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template("users/index.html", users=users)


@app.get("/users/<int:user_id>")
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    return render_template("users/show.html", user=user)


@app.get("/users/<int:user_id>/following")
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template("users/following.html", user=user)


@app.get("/users/<int:user_id>/followers")
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template("users/followers.html", user=user)


@app.post("/users/follow/<int:follow_id>")
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.post("/users/stop-following/<int:follow_id>")
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route("/users/profile", methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    form = UserEditForm(obj=g.user)

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    if form.validate_on_submit():
        is_password_valid = User.authenticate(g.user.username, form.password.data)

        if is_password_valid:
            g.user.username = form.username.data
            g.user.email = form.email.data
            g.user.image_url = (
                form.image_url.data if form.image_url.data != "" else DEFAULT_IMAGE
            )
            g.user.header_image_url = (
                form.header_image_url.data
                if form.header_image_url.data != ""
                else DEFAULT_HEADER_IMAGE
            )
            g.user.bio = form.bio.data

            db.session.commit()
            flash("User Profile Updated!", "success")
            return redirect(f"/users/{g.user.id}")

        else:
            flash("Incorrect Password", "danger")
            return redirect("/")
    else:
        return render_template("/users/edit.html", form=form)


@app.post("/users/delete")
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    if g.csrf_checking.validate_on_submit():

        do_logout()

        Message.query.filter(Message.user_id == g.user.id).delete()
        db.session.delete(g.user)
        db.session.commit()

        flash("User was deleted", "warning")
        return redirect("/signup")


@app.get("/users/<int:user_id>/likes")
def list_liked_messages_for_user(user_id):
    """List all messages liked by a user."""

    user = User.query.get(user_id)

    return render_template("/users/likes.html", user=user)


##############################################################################
# ~~ Messages routes:


@app.route("/messages/new", methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template("messages/new.html", form=form)


@app.get("/messages/<int:message_id>")
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template("messages/show.html", message=msg)


@app.post("/messages/<int:message_id>/delete")
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


##############################################################################
# ~~ Homepage and error pages


@app.get("/")
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users / self
    """

    if g.user:
        following_ids = [f.id for f in g.user.following]
        print(following_ids)
        messages = (
            Message.query.filter(
                or_(Message.user_id.in_(following_ids), Message.user_id == g.user.id)
            )
            .order_by(Message.timestamp.desc())
            .limit(100)
            .all()
        )

        print(messages)

        return render_template("home.html", messages=messages)

    else:
        return render_template("home-anon.html")


##############################################################################
# ~~ Message Like routes:


@app.post("/msg/like/<int:msg_id>")
def like_message(msg_id):
    """Show liked messages and update the database"""

    msg_liked = Message.query.get(msg_id)


# @app.post('/msg/stop-liking/<int:msg_id>')
# def stop_liking_message(msg_id):
#     """Stop liking a liked message and update the DB"""


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask


@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response
