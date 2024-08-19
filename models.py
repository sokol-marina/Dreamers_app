from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
db = SQLAlchemy()


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """
    db.app = app
    db.init_app(app)


class User(db.Model):
    """Site user."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    

    dreams = db.relationship("Dream", backref="user", cascade="all, delete-orphan")

    @classmethod
    def register(cls, username, email, password):
        """Register a user, hashing their password."""
        hashed = bcrypt.generate_password_hash(password).decode("utf8")
        user = cls(username=username, email=email, password=hashed)
        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Validate that user exists & password is correct.
        Return user if valid; else return False.
        """
        user = cls.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            return user
        else:
            return False


class Dream(db.Model):
    """Dream."""

    __tablename__ = "dreams"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dream_description = db.Column(db.Text, nullable=False)
    interpretation = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
