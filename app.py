
from flask import Flask, render_template, redirect, session, flash, request, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Dream
from forms import RegisterForm, LoginForm, DreamForm
from sqlalchemy.exc import IntegrityError
import requests
import os
from dotenv import load_dotenv
from werkzeug.exceptions import Unauthorized

load_dotenv()  # Load environment variables from .env file

# Access the environment variables using os.getenv()
HUGGING_FACE_API_KEY = os.getenv('HUGGING_FACE_API_KEY')


# Database configuration
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('DATABASE_URL')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config["DEBUG"] = True  # Enable debug mode

# Hugging Face API configuration
API_URL = "https://api-inference.huggingface.co/models/gpt2"
headers = {"Authorization": f"Bearer {os.getenv('HUGGING_FACE_API_KEY')}"}

app.debug = True
toolbar = DebugToolbarExtension(app)


def query_huggingface_api(dream_description):
    """Send the dream description to Hugging Face API and get the interpretation."""
    response = requests.post(API_URL, headers=headers, json={"inputs": dream_description})
    response_data = response.json()
    return response_data['choices'][0]['text']

connect_db(app)

@app.route("/")
def homepage():
    """Show homepage with links to site areas."""
    return redirect("/login")

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a user: produce form and handle form submission."""

    if "user_id" in session:
        return redirect(f"/users/{session['user_id']}")

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data

        try:
            user = User.register(username, password, email)
            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id
            return redirect(f"/users/{user.id}")
        except IntegrityError:
            db.session.rollback()  # Roll back the session to avoid incomplete transactions
            form.username.errors.append("Username already taken. Please choose a different one.")
            return render_template("users/register.html", form=form)
    
    return render_template("users/register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Produce login form or handle login."""

    if "id" in session:
        return redirect("/dream")
        # return redirect(f"/users/{session['id']}")

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)  # <User> or False
        if user:
            session['user_id'] = user.id
            return redirect(f"/users/{user.id}")
        else:
            form.username.errors = ["Invalid username/password."]
            return render_template("users/login.html", form=form)

    return render_template("users/login.html", form=form)

@app.route('/logout')
def logout_user():
    """Log the user out and redirect to login."""
    session.pop('user_id', None)  # Use 'None' as a default to avoid KeyError
    flash("Goodbye!", "info")
    return redirect('/login')


@app.route("/users/<int:id>")
def show_user(id):
    """Example page for logged-in-users."""

    if "user_id" not in session or id != session['user_id']:
        raise Unauthorized()

    user = User.query.get_or_404(id)

    return render_template("users/user_details.html", user=user)

@app.route('/submit_dream', methods=['GET', 'POST'])
def submit_dream():
    """Allow a user to submit a dream."""

    if "user_id" not in session:
        flash("Please log in to submit a dream.", "warning")
        return redirect("/login")

    form = DreamForm()

    if form.validate_on_submit():
        dream_description = form.dream_description.data

        # Send the dream description to the Hugging Face API
        interpretation = query_huggingface_api(dream_description)


        # Create a new dream entry
        new_dream = Dream(
            user_id=session['user_id'],
            dream_description=dream_description,
            interpretation=interpretation
        )

        # Add and commit the new dream to the database
        db.session.add(new_dream)
        db.session.commit()

        flash("Dream submitted successfully!", "success")
        return redirect(f"/users/{session['user_id']}")

    return render_template("dreams/submit_dream.html", form=form)
