from datetime import datetime
import sys
import os

# Add parent directory to path to import db
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import db

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    charger_id = db.Column(db.Integer, db.ForeignKey('charger.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, confirmed, completed, cancelled
    payment_id = db.Column(db.String(100), nullable=True)  # Reference to payment transaction
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ratings = db.relationship('Rating', backref='reservation', lazy=True)
    
    def get_duration_hours(self):
        return (self.end_time - self.start_time).total_seconds() / 3600
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'charger_id': self.charger_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'total_price': self.total_price,
            'status': self.status,
            'payment_id': self.payment_id,
            'duration_hours': self.get_duration_hours(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }