from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a real secret key

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Database connection setup
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',  # Replace with your MySQL username
        password='test',  # Replace with your MySQL password
        database='movie_booking'  # Replace with your MySQL database name
    )

@app.route('/')
def home():
    return render_template('home.html')

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", (username, hashed_password, email))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user:
            # User exists, now check password
            if check_password_hash(user[1], password):
                session['user_id'] = user[0]  # Store user ID in session
                logging.debug(f"User ID {user[0]} logged in successfully.")
                flash('Login successful!', 'success')
                return redirect(url_for('movies'))
            else:
                flash('Invalid password.', 'danger')
                logging.debug("Login failed: Invalid password.")
        else:
            flash('Username does not exist.', 'danger')
            logging.debug("Login failed: Username does not exist.")

        cursor.close()
        conn.close()
        
    return render_template('login.html')

# Fetch movies with their showtimes
def fetch_movies_with_showtimes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(""" 
        SELECT m.movie_id, m.title, s.showtime_id, s.time 
        FROM movies m 
        JOIN showtimes s ON m.movie_id = s.movie_id 
    """)
    movies = cursor.fetchall()
    cursor.close()
    conn.close()

    # Structure movies with showtimes
    movies_dict = {}
    for movie_id, title, showtime_id, showtime in movies:
        showtime = str(showtime)  # Convert time to string
        if movie_id not in movies_dict:
            movies_dict[movie_id] = {'title': title, 'showtimes': []}
        movies_dict[movie_id]['showtimes'].append((showtime_id, showtime))

    return movies_dict

@app.route('/movies')
def movies():
    user_id = session.get('user_id')  # Get user_id from session
    user_status = None
    movies = fetch_movies_with_showtimes()  # Fetch movie data with showtimes

    if user_id:
        # Fetch user information if needed
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        user_status = user[0] if user else None

    return render_template('movies.html', user_status=user_status, movies=movies)

@app.route('/book/<int:movie_id>/<int:showtime_id>', methods=['GET', 'POST'])
def bookings(movie_id, showtime_id):
    if request.method == 'POST':
        seats = int(request.form['seats'])
        user_id = session.get('user_id')
        parking_id = request.form.get('parking_id')  # Selected parking ID from the form
        
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert booking into the bookings table
        cursor.execute("INSERT INTO bookings (user_id, movie_id, showtime_id, seats) VALUES (%s, %s, %s, %s)", 
                       (user_id, movie_id, showtime_id, seats))
        booking_id = cursor.lastrowid

        # Check parking availability and reduce only if parking is selected
        if parking_id:
            cursor.execute("SELECT available_spots FROM parking WHERE parking_id = %s", (parking_id,))
            available_spots = cursor.fetchone()[0]

            # Ensure there are enough parking spots
            if available_spots >= seats:
                # Insert into parking_bookings table
                cursor.execute("INSERT INTO parking_bookings (booking_id, parking_id, spots_reserved) VALUES (%s, %s, %s)", 
                               (booking_id, parking_id, seats))
                
                # Reduce available spots
                cursor.execute("UPDATE parking SET available_spots = available_spots - %s WHERE parking_id = %s", 
                               (seats, parking_id))
            else:
                flash('Not enough parking spots available.', 'warning')
                return redirect(url_for('movies'))

        # Commit the transaction
        conn.commit()
        cursor.close()
        conn.close()
        flash('Booking successful!', 'success')
        return redirect(url_for('movies'))

    # Fetch available parking spots for the GET request
    parking_options = fetch_parking_options()
    return render_template('bookings.html', movie_id=movie_id, showtime_id=showtime_id, parking_options=parking_options)

# Function to fetch parking options
def fetch_parking_options():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT parking_id, location, available_spots FROM parking WHERE available_spots > 0")
    parking_options = cursor.fetchall()
    cursor.close()
    conn.close()
    return parking_options

@app.route('/my_bookings', methods=['GET', 'POST'])
def my_bookings():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view your bookings.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # If the request method is POST, handle the cancellation logic
    if request.method == 'POST':
        booking_id = request.form.get('booking_id')
        
        # Set the booking status to "1" (canceled) instead of deleting it
        cursor.execute("UPDATE bookings SET status = 1 WHERE booking_id = %s", (booking_id,))
        conn.commit()
        flash('Booking canceled successfully.', 'success')

    # Fetch all bookings for the user
    cursor.execute(""" 
        SELECT b.booking_id, m.title, s.time, b.seats, p.parking_id 
        FROM bookings b 
        JOIN movies m ON b.movie_id = m.movie_id 
        JOIN showtimes s ON b.showtime_id = s.showtime_id 
        LEFT JOIN parking_bookings p ON b.booking_id = p.booking_id 
        WHERE b.user_id = %s AND b.status = 0
    """, (user_id,))
    bookings = cursor.fetchall()

    cursor.close()
    conn.close()
    
    return render_template('my_bookings.html', bookings=bookings)

@app.route('/finalize_booking', methods=['POST'])
def finalize_booking():
    seats = request.form.get('seats')
    parking = request.form.get('parking')
    # Process the booking logic here (e.g., save to database)
    return redirect(url_for('confirmation_page'))  # Redirect to a confirmation page

@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    booking_id = request.form.get('booking_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET status = 1 WHERE booking_id = %s", (booking_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Booking canceled successfully.', 'success')
    return redirect(url_for('my_bookings'))

@app.route('/booking_details/<int:movie_id>', methods=['GET', 'POST'])
def booking_details(movie_id):
    # Fetch movie details
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM movies WHERE movie_id = %s", (movie_id,))
    movie = cursor.fetchone()

    # Fetch showtimes and parking options
    showtimes = fetch_showtimes_for_movie(movie_id)
    parking_options = fetch_parking_options()

    if request.method == 'POST':
        showtime_id = request.form['showtime_id']
        parking_id = request.form.get('parking_id') if 'need_parking' in request.form else None
        return redirect(url_for('my_bookings', movie_id=movie_id, showtime_id=showtime_id, parking_id=parking_id))

    return render_template('booking_details.html', movie=movie, showtimes=showtimes, parking_options=parking_options)


def fetch_showtimes_for_movie(movie_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT showtime_id, time FROM showtimes WHERE movie_id = %s", (movie_id,))
    showtimes = cursor.fetchall()
    cursor.close()
    conn.close()
    return showtimes

if __name__ == '__main__':
    app.run(debug=True)
