# Smart Parking Management System (Web App)

This is a simple full-stack Parking Management System built with **Flask (Python)**, **HTML**, **CSS**, and **JavaScript**.  
It supports:

- User login (with roles: admin, user)
- Dashboard with key stats
- Vehicle entry and exit management
- Parking spots tracking
- Search by license plate / parking ID
- Admin reports with total earnings between dates

## Project Structure

```
parking-management-system/
├── app.py
├── schema.sql
├── requirements.txt
├── templates/
│   ├── layout.html
│   ├── login.html
│   └── dashboard.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

## How to Run

1. Make sure you have **Python 3.9+** installed.

2. Create and activate a virtual environment (optional but recommended):

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Initialize the database and run the app:

```bash
python app.py
```

On the first run:
- It will create `parking.db`
- It will apply the schema from `schema.sql`
- It will insert some default parking spots
- It will create a default admin user:

> username: **admin**  
> password: **admin123**

5. Open your browser and go to:

```
http://127.0.0.1:5000
```

## Notes

- This project uses SQLite (`parking.db`) for simplicity.  
  You can migrate the schema to MySQL easily by converting `schema.sql` to MySQL dialect.
- For production, make sure to:
  - Change `app.secret_key` in `app.py`
  - Run with a proper WSGI server (e.g., gunicorn, uWSGI)
  - Use a stronger password for the admin user
