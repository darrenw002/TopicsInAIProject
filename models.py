from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

# Resource Model for storing various AI resources
class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # e.g., "Tutorial", "Research", "GitHub", "Blog"
    link = db.Column(db.String(500), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    approved = db.Column(db.Boolean, default=True)  # For user-submitted resources, admin can toggle

# User Model for authentication & bookmarking
# Inherit from db.Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Flask-Login requirements:
    @property
    def is_active(self):
        # For this simple app, return True always
        return True

    @property
    def is_authenticated(self):
        # Return True if the user has valid credentials
        return True

    @property
    def is_anonymous(self):
        # Return True only if the user is not logged in
        return False

    def get_id(self):
        # Return the user ID as a string
        return str(self.id)

    

# Bookmark Model - many-to-many relationship
class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=False)
