# ChargeShare

ChargeShare is a web application that enables electric vehicle owners to share their private charging stations when they're not in use. This creates a win-win situation where charger owners can earn money from their investment, and EV drivers get access to more charging options.

## Features

- **For Charger Owners:**
  - Register and manage your charging stations
  - Set availability and pricing
  - Accept reservation requests
  - Track earnings
  - Receive ratings and feedback

- **For EV Drivers:**
  - Find nearby available chargers on a map
  - Make reservations for charging
  - Secure payment processing
  - Rate and review your experience
  - Manage your charging history

## Technology Stack

- **Backend:**
  - Flask (Python web framework)
  - SQLAlchemy (ORM)
  - SQLite (Database)
  - Flask-Login (Authentication)

- **Frontend:**
  - HTML/CSS/JavaScript
  - Bootstrap 5
  - Interactive map interface (placeholder)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/chargeshare.git
   cd chargeshare
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install flask flask-sqlalchemy flask-login 
   ```

4. Run the application:
   ```
   python app.py
   ```

5. Navigate to `http://localhost:5000` in your browser

## Project Structure

```
chargeshare/
├── app.py                  # Main application file
├── models/                 # Database models
│   ├── user.py             # User model
│   ├── charger.py          # Charger model
│   ├── reservation.py      # Reservation model
│   └── rating.py           # Rating model
├── templates/              # HTML templates
│   ├── index.html          # Landing page
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   └── dashboard.html      # User dashboard
└── static/                 # Static files (CSS, JS, images)
    └── images/             # Image files
```

## API Endpoints

The application provides RESTful API endpoints for the mobile application:

- `GET /api/chargers`: Get a list of available chargers
- `GET /api/chargers/<id>`: Get details for a specific charger
- `POST /api/register`: Register a new user
- `POST /api/login`: Authenticate a user
- `POST /api/reservations`: Create a new reservation
- `GET /api/reservations/<id>`: Get details for a specific reservation
- `POST /api/reservations/<id>/complete`: Complete a reservation
- `POST /api/ratings`: Submit a rating

## Future Development

- Integration with payment processing
- Real-time availability updates
- Mobile app development
- Smart charger integration
- Advanced reservation management
- Proximity-based search

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributors

- Your Name - Initial work

## Acknowledgments

- ChargeShare was developed as a conceptual project
- Inspired by the growing need for EV charging infrastructure