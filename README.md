# 🎬 Movie Ticket Booking System

A web application built using **Flask** and **MySQL** that allows users to register, log in, browse available movies, book tickets, reserve parking spots, and manage their bookings.

---

## 🚀 Features
- User Registration and Login (with secure password hashing)
- Browse Movies and Showtimes
- Ticket Booking System
- Parking Spot Reservation
- View and Cancel Bookings
- Flash Messages for User Feedback
- Session Management
- Logging for Debugging and Monitoring

---

## 🛠 Tech Stack
- **Backend**: Python (Flask)
- **Database**: MySQL
- **Frontend**: HTML, CSS (Jinja Templates)
- **Authentication**: Werkzeug Security (password hashing)
- **Other**: Session Management, Logging

---

## 📂 Project Structure
```
├── app.py
├── templates/
│   ├── home.html
│   ├── register.html
│   ├── login.html
│   ├── movies.html
│   ├── bookings.html
│   ├── my_bookings.html
│   ├── booking_details.html
├── static/
│   └── (CSS/JS Files)
├── requirements.txt
└── README.md
```

---

## 🧠 Database Tables
You will need these main tables:

- `users`
- `movies`
- `showtimes`
- `bookings`
- `parking`
- `parking_bookings`

---

## 🏁 How to Run Locally
1. Clone the repository.
2. Set up a MySQL database and update connection settings inside \`app.py\`.
3. Install dependencies:
    ```bash
    pip install flask mysql-connector-python werkzeug
    ```
4. Run the server:
    ```bash
    python app.py
    ```
5. Visit `http://127.0.0.1:5000/` in your browser.

---

## ❤️ Acknowledgements
- **Flask** documentation
- **MySQL** official documentation
- **Werkzeug** for secure password hashing
- Special thanks to the Flask and Python open-source community!

