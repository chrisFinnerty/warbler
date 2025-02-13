import os

from dotenv import load_dotenv
from flask import Flask, render_template, request, flash, redirect, session, g, url_for, abort
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine

from forms import UserAddForm, LoginForm, MessageForm, EditProfileForm
from models import db, connect_db, User, Message, Likes

CURR_USER_KEY = "curr_user"
load_dotenv()

def create_app(db_name, testing=False):
    app = Flask(__name__)
    
    # Get DB_URI from environ variable (useful for production/testing) or,
    # if not set there, use development local db.
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        os.environ.get('DATABASE_URL', f'postgresql:///{db_name}'))

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = False
    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")

    if testing:
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_ECHO'] = True

    # toolbar = DebugToolbarExtension(app)

    # connect_db(app)

    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    try:
        with engine.connect() as connection:
            print("Database connection successful")
    except Exception as e:
        print(f'Database connection failed: {eval}')


    ##############################################################################
    # User signup/login/logout


    @app.before_request
    def add_user_to_g():
        """If we're logged in, add curr user to Flask global."""

        if CURR_USER_KEY in session:
            g.user = User.query.get(session[CURR_USER_KEY])

        else:
            g.user = None


    def do_login(user):
        """Log in user."""

        session[CURR_USER_KEY] = user.id


    def do_logout():
        """Logout user."""

        if CURR_USER_KEY in session:
            del session[CURR_USER_KEY]


    @app.route('/signup', methods=["GET", "POST"])
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
                flash("Username already taken", 'danger')
                return render_template('users/signup.html', form=form)

            do_login(user)

            return redirect("/")

        else:
            return render_template('users/signup.html', form=form)


    @app.route('/login', methods=["GET", "POST"])
    def login():
        """Handle user login."""

        form = LoginForm()

        if form.validate_on_submit():
            user = User.authenticate(form.username.data,
                                    form.password.data)

            if user:
                do_login(user)
                flash(f"Hello, {user.username}!", "success")
                return redirect("/")

            flash("Invalid credentials.", 'danger')

        return render_template('users/login.html', form=form)


    @app.route('/logout')
    def logout():
        """Handle logout of user."""
        do_logout()
        flash("Successfully logged out.", 'success')

        return redirect('/login')



    ##############################################################################
    # General user routes:

    @app.route('/users')
    def list_users():
        """Page with listing of users.

        Can take a 'q' param in querystring to search by that username.
        """

        search = request.args.get('q')

        if not search:
            users = User.query.all()
        else:
            users = User.query.filter(User.username.like(f"%{search}%")).all()

        return render_template('users/index.html', users=users)


    @app.route('/users/<int:user_id>', methods=['GET', 'POST'])
    def users_show(user_id):
        """Show user profile."""

        user = User.query.get_or_404(user_id)
        liked_message_ids = []

        likes_count = len(user.likes)

        # snagging messages in order from the database;
        # user.messages won't be in order by default
        messages = (Message
                    .query
                    .filter(Message.user_id == user_id)
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())
        
 
        likes = (Likes.query.filter_by(user_id=user_id).all())
        liked_message_ids = {like.message_id for like in likes}
        
        location = user.location
        bio = user.bio
        header_image_url = user.header_image_url

        if request.method == 'POST':
            if not g.user or g.user.id != user_id:
                flash('Access unauthorized.', 'danger')
                return redirect('/')
            
            message_id = request.form.get('message_id')
            was_liked = toggle_like_message(g.user.id, message_id)
            liked_message_ids = set(Likes.query.filter_by(user_id=user_id).all())

        return render_template('users/show.html', user=user, messages=messages, location=location, bio=bio, header_image_url=header_image_url, likes_count=likes_count, liked_message_ids=liked_message_ids)


    @app.route('/users/<int:user_id>/following')
    def show_following(user_id):
        """Show list of people this user is following."""

        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect("/")

        user = User.query.get_or_404(user_id)

        likes_count = len(user.likes)
        
        return render_template('users/following.html', user=user, likes_count=likes_count)


    @app.route('/users/<int:user_id>/followers')
    def users_followers(user_id):
        """Show list of followers of this user."""

        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect("/")

        user = User.query.get_or_404(user_id)
        likes_count = len(user.likes)

        return render_template('users/followers.html', user=user, likes_count=likes_count)


    @app.route('/users/follow/<int:follow_id>', methods=['POST'])
    def add_follow(follow_id):
        """Add a follow for the currently-logged-in user."""

        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect("/")

        followed_user = User.query.get_or_404(follow_id)
        g.user.following.append(followed_user)
        db.session.commit()

        return redirect(f"/users/{g.user.id}/following")


    @app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
    def stop_following(follow_id):
        """Have currently-logged-in-user stop following this user."""

        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect("/")

        followed_user = User.query.get(follow_id)
        g.user.following.remove(followed_user)
        db.session.commit()

        return redirect(f"/users/{g.user.id}/following")


    @app.route('/users/profile', methods=["GET", "POST"])
    def edit_profile():
        """Update profile for current user."""
        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect("/")
        
        form = EditProfileForm()

        if form.validate_on_submit():
            try:
                user = User.authenticate(
                    username=form.username.data,
                    password=form.password.data
                )
            except User.AuthenticationError:
                flash("Incorrect password.", 'danger')
                return redirect('/')
            
            g.user.email = form.email.data
            g.user.image_url = form.image_url.data
            g.user.header_image_url = form.header_image_url.data
            g.user.bio = form.bio.data

            db.session.commit()

            return redirect(url_for('users_show', user_id=g.user.id))
        return render_template('users/edit.html', user=g.user, form=form)
            

    @app.route('/users/delete', methods=["POST"])
    def delete_user():
        """Delete user."""

        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect("/")

        do_logout()

        db.session.delete(g.user)
        db.session.commit()

        return redirect("/signup")


    ##############################################################################
    # Messages routes:

    @app.route('/messages/new', methods=["GET", "POST"])
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

        return render_template('messages/new.html', form=form)


    @app.route('/messages/<int:message_id>', methods=["GET", "POST"])
    def messages_show(message_id):
        """Show a message. Also added functionality to like the message in this view."""

        msg = Message.query.get(message_id)
        like = Likes.query.filter_by(user_id=g.user.id, message_id=message_id).first()

        if msg is None:
            abort(404)
        
        if request.method == 'POST':
            if not g.user or g.user.id != msg.user_id:
                flash('Access unauthorized.', 'danger')
                return redirect('/')
            
            was_liked = toggle_like_message(g.user.id, message_id)

            return redirect(url_for('messages_show'), message_id=message_id)
        
        return render_template('messages/show.html', message=msg, like=like)


    @app.route('/messages/<int:message_id>/delete', methods=["POST"])
    def messages_destroy(message_id):
        """Delete a message."""

        if not g.user:
            flash("Access unauthorized", "danger")
            return redirect("/")

        msg = Message.query.get(message_id)

        if msg.user_id != g.user.id:
            flash('Access unauthorized', 'danger')
            return redirect('/')
        
        db.session.delete(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")


    ##############################################################################
    # Likes routes:

    def toggle_like_message(user_id, message_id):
        """Used to toggle likes on messages (like/unlike)."""

        like = Likes.query.filter_by(user_id=user_id, message_id=message_id).first()

        if like:
            db.session.delete(like)
            db.session.commit()
            return False
        else:
            new_like = Likes(user_id=user_id, message_id=message_id)
            db.session.add(new_like)
            db.session.commit()
            return True
        
    @app.route('/users/add-like/<int:msg_id>', methods=['POST'])
    def like_msg(msg_id):
        """Post route to like a message."""

        if not g.user:
            flash('Access unauthorized.', 'danger')
            return redirect('/')
        
        was_liked = toggle_like_message(g.user.id, msg_id)
        
        return redirect(request.referrer)
    
    @app.route('/users/<int:user_id>/liked-messages')
    def show_liked_messages(user_id):
        """Route user to see what messages they have liked. 
        Originates from user clicking "Likes" link on any user profile."""

        if not g.user:
            flash('Access unauthorized.', 'danger')
            return('/')
        
        user = User.query.get_or_404(user_id)
        
        liked_messages = Message.query.join(Likes).filter(Likes.user_id == user_id).order_by(Message.timestamp.desc()).all()
        likes_count = len(user.likes)

        return render_template('/messages/liked-messages.html', user=user, liked_messages=liked_messages, likes_count=likes_count)

    ##############################################################################
    # Homepage and error pages


    @app.route('/')
    def homepage():
        """Show homepage:

        - anon users: no messages
        - logged in: 100 most recent messages of followed_users
        """

        if g.user:
            following_ids = [user.id for user in g.user.following]
            messages = (Message
                        .query
                        .filter(Message.user_id.in_(following_ids))
                        .order_by(Message.timestamp.desc())
                        .limit(100)
                        .all())
            likes = (Likes.query.filter(Likes.user_id == g.user.id).all())
            liked_message_ids = {like.message_id for like in likes}

            return render_template('home.html', messages=messages, likes=likes, liked_message_ids=liked_message_ids)

        else:
            return render_template('home-anon.html')


    ##############################################################################
    # Turn off all caching in Flask
    #   (useful for dev; in production, this kind of stuff is typically
    #   handled elsewhere)
    #
    # https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

    @app.after_request
    def add_header(req):
        """Add non-caching headers on every request."""

        req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        req.headers["Pragma"] = "no-cache"
        req.headers["Expires"] = "0"
        req.headers['Cache-Control'] = 'public, max-age=0'
        return req
    
    return app

# if __name__ == '__main__':
#     app = create_app(os.environ.get('DATABASE_URL'), testing=True)
#     print(os.environ.get('DATABASE_URL'))
#     app.run(debug=True)