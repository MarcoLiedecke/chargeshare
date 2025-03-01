from datetime import datetime
import sys
import os

# Add parent directory to path to import db
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import db

class Charger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    charger_type = db.Column(db.String(50), nullable=False)  # e.g., 'Type 2', 'CCS', 'CHAdeMO'
    power_output = db.Column(db.Float, nullable=False)  # in kW
    price_per_hour = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reservations = db.relationship('Reservation', backref='charger', lazy=True)
    
    def get_average_rating(self):
        from models.reservation import Reservation
        from models.rating import Rating
        
        reservations = Reservation.query.filter_by(charger_id=self.id).all()
        reservation_ids = [r.id for r in reservations]
        
        if not reservation_ids:
            return 0
        
        ratings = Rating.query.filter(Rating.reservation_id.in_(reservation_ids)).all()
        ratings_values = [r.rating for r in ratings]
        
        return sum(ratings_values) / len(ratings_values) if ratings_values else 0
    
    def is_available(self, start_time, end_time):
        from models.reservation import Reservation
        
        conflicting_reservation = Reservation.query.filter_by(
            charger_id=self.id,
            status='confirmed'
        ).filter(
            (Reservation.start_time <= end_time) & (Reservation.end_time >= start_time)
        ).first()
        
        return conflicting_reservation is None
    
    def to_dict(self):
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'name': self.name,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'charger_type': self.charger_type,
            'power_output': self.power_output,
            'price_per_hour': self.price_per_hour,
            'is_active': self.is_active,
            'average_rating': self.get_average_rating(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }