from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os

# Import db instance
from models.database import db
# Import models
from models.user import User

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chargeshare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database with app
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
from models.charger import Charger
from models.reservation import Reservation
from models.rating import Rating

@login_manager.user_loader
def load_user(user_id):
    # Updated to use Session.get() instead of Query.get() to fix the deprecation warning
    return db.session.get(User, int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# User authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.')
            return redirect(url_for('register'))
        
        new_user = User(email=email, name=name)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully!')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))
        
        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_chargers = Charger.query.filter_by(owner_id=current_user.id).all()
    user_reservations = Reservation.query.filter_by(user_id=current_user.id).all()
    
    # Calculate total earnings
    total_earnings = 0
    for charger in user_chargers:
        completed_reservations = Reservation.query.filter_by(
            charger_id=charger.id,
            status='completed'
        ).all()
        
        for reservation in completed_reservations:
            total_earnings += reservation.total_price
    
    return render_template('dashboard.html', 
                          chargers=user_chargers, 
                          reservations=user_reservations,
                          total_earnings=total_earnings)

# Charger routes
@app.route('/chargers', methods=['GET'])
def get_chargers():
    latitude = request.args.get('lat', type=float)
    longitude = request.args.get('lng', type=float)
    
    # For a real application, you would implement proximity search
    # Here we just return all chargers for simplicity
    chargers = Charger.query.filter_by(is_active=True).all()
    
    return jsonify([charger.to_dict() for charger in chargers])

@app.route('/chargers/<int:charger_id>', methods=['GET'])
def get_charger(charger_id):
    charger = Charger.query.get_or_404(charger_id)
    return jsonify(charger.to_dict())

@app.route('/chargers', methods=['POST'])
@login_required
def create_charger():
    data = request.json
    
    new_charger = Charger(
        owner_id=current_user.id,
        name=data.get('name'),
        address=data.get('address'),
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        charger_type=data.get('charger_type'),
        power_output=data.get('power_output'),
        price_per_hour=data.get('price_per_hour'),
        is_active=True
    )
    
    db.session.add(new_charger)
    db.session.commit()
    
    return jsonify(new_charger.to_dict()), 201

@app.route('/chargers/<int:charger_id>', methods=['PUT'])
@login_required
def update_charger(charger_id):
    charger = Charger.query.get_or_404(charger_id)
    
    if charger.owner_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    
    charger.name = data.get('name', charger.name)
    charger.address = data.get('address', charger.address)
    charger.latitude = data.get('latitude', charger.latitude)
    charger.longitude = data.get('longitude', charger.longitude)
    charger.charger_type = data.get('charger_type', charger.charger_type)
    charger.power_output = data.get('power_output', charger.power_output)
    charger.price_per_hour = data.get('price_per_hour', charger.price_per_hour)
    charger.is_active = data.get('is_active', charger.is_active)
    
    db.session.commit()
    
    return jsonify(charger.to_dict())

# Reservation routes
@app.route('/reservations', methods=['POST'])
@login_required
def create_reservation():
    data = request.json
    
    charger_id = data.get('charger_id')
    start_time = datetime.fromisoformat(data.get('start_time'))
    end_time = datetime.fromisoformat(data.get('end_time'))
    
    charger = Charger.query.get_or_404(charger_id)
    
    # Check if charger is available during requested time
    conflicting_reservation = Reservation.query.filter_by(
        charger_id=charger_id,
        status='confirmed'
    ).filter(
        (Reservation.start_time <= end_time) & (Reservation.end_time >= start_time)
    ).first()
    
    if conflicting_reservation:
        return jsonify({'error': 'Charger is not available during this time'}), 400
    
    # Calculate price
    duration_hours = (end_time - start_time).total_seconds() / 3600
    total_price = duration_hours * charger.price_per_hour
    
    new_reservation = Reservation(
        user_id=current_user.id,
        charger_id=charger_id,
        start_time=start_time,
        end_time=end_time,
        total_price=total_price,
        status='confirmed'  # In a real app, this would be 'pending' until payment
    )
    
    db.session.add(new_reservation)
    db.session.commit()
    
    # In a real app, you would handle payment processing here
    
    return jsonify(new_reservation.to_dict()), 201

@app.route('/reservations/<int:reservation_id>', methods=['GET'])
@login_required
def get_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    
    if reservation.user_id != current_user.id and Charger.query.get(reservation.charger_id).owner_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(reservation.to_dict())

@app.route('/reservations/<int:reservation_id>/complete', methods=['POST'])
@login_required
def complete_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    
    if reservation.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    reservation.status = 'completed'
    db.session.commit()
    
    return jsonify(reservation.to_dict())

# Rating routes
@app.route('/ratings', methods=['POST'])
@login_required
def create_rating():
    data = request.json
    
    new_rating = Rating(
        reservation_id=data.get('reservation_id'),
        rater_id=current_user.id,
        rated_id=data.get('rated_id'),
        rating=data.get('rating'),
        comment=data.get('comment', '')
    )
    
    db.session.add(new_rating)
    db.session.commit()
    
    return jsonify(new_rating.to_dict()), 201

# API for mobile app
@app.route('/api/chargers', methods=['GET'])
def api_get_chargers():
    latitude = request.args.get('lat', type=float)
    longitude = request.args.get('lng', type=float)
    
    # For a real application, you would implement proximity search
    chargers = Charger.query.filter_by(is_active=True).all()
    
    return jsonify([charger.to_dict() for charger in chargers])

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    
    user = User.query.filter_by(email=data.get('email')).first()
    if user:
        return jsonify({'error': 'Email already exists'}), 400
    
    new_user = User(email=data.get('email'), name=data.get('name'))
    new_user.set_password(data.get('password'))
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    
    user = User.query.filter_by(email=data.get('email')).first()
    if not user or not user.check_password(data.get('password')):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # In a real app, you would generate and return a token here
    return jsonify({'user_id': user.id, 'name': user.name, 'email': user.email})

def create_sample_data():
    """Create sample data if the database is empty"""
    if User.query.first():
        # Database already has data
        return
    
    # Create sample users
    users = [
        {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'password123',
            'phone': '+45 12345678'
        },
        {
            'name': 'Alice Smith',
            'email': 'alice@example.com',
            'password': 'password123',
            'phone': '+45 87654321'
        },
        {
            'name': 'Bob Johnson',
            'email': 'bob@example.com',
            'password': 'password123',
            'phone': '+45 23456789'
        },
        {
            'name': 'Emma Nielsen',
            'email': 'emma@example.com',
            'password': 'password123',
            'phone': '+45 34567890'
        },
        {
            'name': 'Michael Hansen',
            'email': 'michael@example.com',
            'password': 'password123',
            'phone': '+45 45678901'
        }
    ]
    
    created_users = []
    for user_data in users:
        user = User(
            name=user_data['name'],
            email=user_data['email'],
            phone=user_data['phone']
        )
        user.set_password(user_data['password'])
        db.session.add(user)
        created_users.append(user)
    
    db.session.commit()
    
    # Create sample chargers
    chargers = [
        {
            'owner': created_users[0],
            'name': 'Central Station Charger',
            'address': 'Bernstorffsgade 16, 1577 København',
            'latitude': 55.6728,
            'longitude': 12.5646,
            'charger_type': 'Type 2',
            'power_output': 22.0,
            'price_per_hour': 45.0
        },
        {
            'owner': created_users[1],
            'name': 'Nørreport Fast Charger',
            'address': 'Frederiksborggade 18, 1360 København',
            'latitude': 55.6833,
            'longitude': 12.5714,
            'charger_type': 'CCS',
            'power_output': 150.0,
            'price_per_hour': 95.0
        },
        {
            'owner': created_users[2],
            'name': 'Østerbro Residential',
            'address': 'Jagtvej 88, 2100 København',
            'latitude': 55.6986,
            'longitude': 12.5542,
            'charger_type': 'Type 2',
            'power_output': 11.0,
            'price_per_hour': 32.0
        },
        {
            'owner': created_users[3],
            'name': 'Amager Beach Charger',
            'address': 'Amager Strandvej 110, 2300 København',
            'latitude': 55.6584,
            'longitude': 12.6318,
            'charger_type': 'CHAdeMO',
            'power_output': 50.0,
            'price_per_hour': 65.0
        },
        {
            'owner': created_users[4],
            'name': 'Frederiksberg Gardens',
            'address': 'Pile Allé, 2000 Frederiksberg',
            'latitude': 55.6722,
            'longitude': 12.5258,
            'charger_type': 'Tesla',
            'power_output': 16.5,
            'price_per_hour': 55.0
        }
    ]
    
    created_chargers = []
    for charger_data in chargers:
        charger = Charger(
            owner_id=charger_data['owner'].id,
            name=charger_data['name'],
            address=charger_data['address'],
            latitude=charger_data['latitude'],
            longitude=charger_data['longitude'],
            charger_type=charger_data['charger_type'],
            power_output=charger_data['power_output'],
            price_per_hour=charger_data['price_per_hour'],
            is_active=True
        )
        db.session.add(charger)
        created_chargers.append(charger)
    
    db.session.commit()
    
    # Create sample reservations
    from datetime import timedelta
    
    reservations = [
        {
            'user': created_users[1],
            'charger': created_chargers[0],
            'start_time': datetime.utcnow() - timedelta(days=5, hours=2),
            'end_time': datetime.utcnow() - timedelta(days=5),
            'status': 'completed'
        },
        {
            'user': created_users[2],
            'charger': created_chargers[0],
            'start_time': datetime.utcnow() - timedelta(days=2, hours=3),
            'end_time': datetime.utcnow() - timedelta(days=2, hours=1),
            'status': 'completed'
        },
        {
            'user': created_users[3],
            'charger': created_chargers[1],
            'start_time': datetime.utcnow() - timedelta(days=1, hours=4),
            'end_time': datetime.utcnow() - timedelta(days=1, hours=2),
            'status': 'completed'
        },
        {
            'user': created_users[0],
            'charger': created_chargers[2],
            'start_time': datetime.utcnow() + timedelta(days=1, hours=10),
            'end_time': datetime.utcnow() + timedelta(days=1, hours=12),
            'status': 'confirmed'
        },
        {
            'user': created_users[4],
            'charger': created_chargers[3],
            'start_time': datetime.utcnow() + timedelta(hours=5),
            'end_time': datetime.utcnow() + timedelta(hours=7),
            'status': 'confirmed'
        }
    ]
    
    created_reservations = []
    for res_data in reservations:
        duration_hours = (res_data['end_time'] - res_data['start_time']).total_seconds() / 3600
        total_price = duration_hours * res_data['charger'].price_per_hour
        
        reservation = Reservation(
            user_id=res_data['user'].id,
            charger_id=res_data['charger'].id,
            start_time=res_data['start_time'],
            end_time=res_data['end_time'],
            total_price=total_price,
            status=res_data['status']
        )
        db.session.add(reservation)
        created_reservations.append(reservation)
    
    db.session.commit()
    
    # Create sample ratings
    ratings = [
        {
            'reservation': created_reservations[0],
            'rater': created_users[1],  # User who used the charger
            'rated': created_users[0],  # Charger owner
            'rating': 5,
            'comment': 'Great charger, very convenient location!'
        },
        {
            'reservation': created_reservations[1],
            'rater': created_users[2],
            'rated': created_users[0],
            'rating': 4,
            'comment': 'Good experience, but charger was a bit slow.'
        },
        {
            'reservation': created_reservations[2],
            'rater': created_users[3],
            'rated': created_users[1],
            'rating': 5,
            'comment': 'Super fast charging, will use again!'
        }
    ]
    
    for rating_data in ratings:
        rating = Rating(
            reservation_id=rating_data['reservation'].id,
            rater_id=rating_data['rater'].id,
            rated_id=rating_data['rated'].id,
            rating=rating_data['rating'],
            comment=rating_data['comment']
        )
        db.session.add(rating)
    
    db.session.commit()
    print('Sample data created successfully!')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_sample_data()
    app.run(debug=True)