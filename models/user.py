from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from models.database import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    chargers = db.relationship('Charger', backref='owner', lazy=True)
    reservations = db.relationship('Reservation', backref='user', lazy=True)
    ratings_given = db.relationship('Rating', foreign_keys='Rating.rater_id', backref='rater', lazy=True)
    ratings_received = db.relationship('Rating', foreign_keys='Rating.rated_id', backref='rated', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_average_rating(self):
        ratings = [r.rating for r in self.ratings_received]
        return sum(ratings) / len(ratings) if ratings else 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'average_rating': self.get_average_rating(),
            'created_at': self.created_at.isoformat()
        }