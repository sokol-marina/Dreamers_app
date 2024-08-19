
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

# Database configuration
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('DATABASE_URL')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config["DEBUG"] = True  # Enable debug mode

# Hugging Face API configuration
API_URL = "https://api-inference.huggingface.co/models/openai-community/gpt2"
headers = {"Authorization": f"Bearer {os.getenv('HUGGING_FACE_API_KEY')}"}

app.debug = True

connect_db(app)

def query_huggingface_api(dream_description):
    """Send the dream description to Hugging Face API and get the interpretation."""
    try:
        prompt = f"Please interpret the following dream: {dream_description}"
        response = requests.post(API_URL, headers=headers,json={"inputs": prompt})
        # Print or log the response code
        print(f"Response Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
        response_data = response.json()
        
        # Check if the response has the expected structure
        if isinstance(response_data, list) and len(response_data) > 0 and 'generated_text' in response_data[0]:
            generated_text = response_data[0]['generated_text']
            # Remove the prompt from the generated text if it's included
            clean_text = generated_text.replace(prompt, '').strip()
            # Update the text in response
            response_data[0]['generated_text'] = clean_text  
            return response_data  # Return the list with generated text
        else:
            return [{"generated_text": "No interpretation available."}]
    except requests.exceptions.RequestException as e:
        print(f"Error querying Hugging Face API: {e}")
        return [{"generated_text": "An error occurred while querying the API."}]

@app.route("/",methods=['GET', 'POST'])
def submit_dream():
    """Allow a user to submit a dream."""
    interpretation = None
    form = DreamForm()

    if form.validate_on_submit():
        dream_description = form.dream_description.data
        result = query_huggingface_api(dream_description)
        # Send the dream description to the Hugging Face API
        interpretation = result[0]['generated_text']

        if "user_id" in session:
        # User is logged in, save the dream interpretation to the database
            new_dream = Dream(
                user_id=session['user_id'],
                dream_description=dream_description,
                interpretation=interpretation
            )

            # # Add and commit the new dream to the database
            db.session.add(new_dream)
            db.session.commit()

            flash("Dream submitted successfully!", "success")
            # return redirect(f"/users/{session['user_id']}")
        else:
            # User is not logged in, just show the interpretation without saving
            flash("Dream interpreted, but not saved. Log in to save your dreams.", "info")

    return render_template("dreams/submit_dream.html", form=form, interpretation=interpretation)


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

    if "user_id" in session:
        return redirect("/")

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)  # <User> or False
        if user:
            session['user_id'] = user.id
            session['username'] = user.username  
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


@app.route("/users/<int:user_id>")
def show_user(user_id):
    """Example page for logged-in-users."""

    if "user_id" not in session or user_id != session['user_id']:
        raise Unauthorized()

    user = User.query.get_or_404(user_id)

    # Get page number from query string (default to 1)
    page = request.args.get('page', 1, type=int)

    # Paginate the dreams, showing 5 per page
    dreams = Dream.query.filter_by(user_id=user.id).order_by(Dream.timestamp.desc()).paginate(page=page, per_page=5)

    return render_template("users/user_details.html", user=user,  dreams=dreams)

