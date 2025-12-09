from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "parking.db")

app = Flask(__name__)
app.secret_key = "change_this_secret_key"  # replace in production


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with app.app_context():
        conn = get_db_connection()
        with open(os.path.join(BASE_DIR, "schema.sql"), "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        # create default admin user if not exists
        cur = conn.execute("SELECT * FROM users WHERE username = ?", ("admin",))
        if cur.fetchone() is None:
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("admin", generate_password_hash("admin123"), "admin"),
            )
        conn.commit()
        conn.close()


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    total_spots = conn.execute("SELECT COUNT(*) as c FROM parking_spots").fetchone()["c"]
    occupied_spots = conn.execute(
        "SELECT COUNT(*) as c FROM parking_spots WHERE is_occupied = 1"
    ).fetchone()["c"]
    active_sessions = conn.execute(
        "SELECT COUNT(*) as c FROM parking_sessions WHERE exit_time IS NULL"
    ).fetchone()["c"]
    conn.close()

    return render_template(
        "dashboard.html",
        username=session.get("username"),
        role=session.get("role"),
        total_spots=total_spots,
        occupied_spots=occupied_spots,
        free_spots=total_spots - occupied_spots,
        active_sessions=active_sessions,
    )


# --- API endpoints ---

@app.route("/api/vehicles", methods=["POST"])
def api_register_entry():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    license_plate = data.get("license_plate", "").upper().strip()
    vehicle_type = data.get("vehicle_type", "car").strip().lower()
    spot_number = data.get("spot_number")

    if not license_plate or not spot_number:
        return jsonify({"error": "license_plate and spot_number are required"}), 400

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()

    # check if spot is free
    spot = conn.execute(
        "SELECT * FROM parking_spots WHERE spot_number = ?", (spot_number,)
    ).fetchone()
    if not spot:
        conn.close()
        return jsonify({"error": "Invalid spot number"}), 400
    if spot["is_occupied"]:
        conn.close()
        return jsonify({"error": "Spot already occupied"}), 400

    # create or find vehicle
    vehicle = conn.execute(
        "SELECT * FROM vehicles WHERE license_plate = ?", (license_plate,)
    ).fetchone()
    if not vehicle:
        conn.execute(
            "INSERT INTO vehicles (license_plate, vehicle_type) VALUES (?, ?)",
            (license_plate, vehicle_type),
        )
        vehicle_id = conn.execute(
            "SELECT last_insert_rowid() as id"
        ).fetchone()["id"]
    else:
        vehicle_id = vehicle["id"]

    conn.execute(
        "INSERT INTO parking_sessions (vehicle_id, entry_time, spot_number) VALUES (?, ?, ?)",
        (vehicle_id, now, spot_number),
    )
    conn.execute(
        "UPDATE parking_spots SET is_occupied = 1 WHERE spot_number = ?", (spot_number,)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Vehicle entry recorded", "entry_time": now})


def calculate_fee(entry_time_str, exit_time_str, vehicle_type):
    fmt = "%Y-%m-%d %H:%M:%S"
    entry_time = datetime.strptime(entry_time_str, fmt)
    exit_time = datetime.strptime(exit_time_str, fmt)
    duration = exit_time - entry_time
    hours = duration.total_seconds() / 3600
    hours = int(hours) + (1 if hours % 1 > 0 else 0)  # round up to next hour

    base_rate = 20  # per hour
    if vehicle_type == "bike":
        base_rate = 10
    elif vehicle_type == "truck":
        base_rate = 40

    return hours * base_rate


@app.route("/api/vehicles/exit", methods=["POST"])
def api_register_exit():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    license_plate = data.get("license_plate", "").upper().strip()

    if not license_plate:
        return jsonify({"error": "license_plate is required"}), 400

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()

    session_row = conn.execute(
        """
        SELECT ps.id, ps.entry_time, ps.spot_number, v.vehicle_type
        FROM parking_sessions ps
        JOIN vehicles v ON ps.vehicle_id = v.id
        WHERE v.license_plate = ? AND ps.exit_time IS NULL
        ORDER BY ps.entry_time DESC
        LIMIT 1
        """,
        (license_plate,),
    ).fetchone()

    if not session_row:
        conn.close()
        return jsonify({"error": "No active session for this vehicle"}), 404

    fee = calculate_fee(session_row["entry_time"], now, session_row["vehicle_type"])

    conn.execute(
        """
        UPDATE parking_sessions
        SET exit_time = ?, total_fee = ?
        WHERE id = ?
        """,
        (now, fee, session_row["id"]),
    )
    conn.execute(
        "UPDATE parking_spots SET is_occupied = 0 WHERE spot_number = ?",
        (session_row["spot_number"],),
    )
    conn.commit()
    conn.close()

    return jsonify(
        {
            "message": "Vehicle exit recorded",
            "exit_time": now,
            "total_fee": fee,
            "spot_number": session_row["spot_number"],
        }
    )


@app.route("/api/sessions/active")
def api_active_sessions():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT ps.id, v.license_plate, v.vehicle_type, ps.entry_time, ps.spot_number
        FROM parking_sessions ps
        JOIN vehicles v ON ps.vehicle_id = v.id
        WHERE ps.exit_time IS NULL
        ORDER BY ps.entry_time DESC
        """
    ).fetchall()
    conn.close()

    sessions = [dict(row) for row in rows]
    return jsonify(sessions)


@app.route("/api/sessions/search")
def api_search_sessions():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    license_plate = request.args.get("license_plate", "").upper().strip()
    parking_id = request.args.get("parking_id", "").strip()

    conn = get_db_connection()
    query = """
        SELECT ps.id, v.license_plate, v.vehicle_type, ps.entry_time,
               ps.exit_time, ps.total_fee, ps.spot_number
        FROM parking_sessions ps
        JOIN vehicles v ON ps.vehicle_id = v.id
        WHERE 1 = 1
    """
    params = []

    if license_plate:
        query += " AND v.license_plate = ?"
        params.append(license_plate)

    if parking_id:
        query += " AND ps.id = ?"
        params.append(parking_id)

    query += " ORDER BY ps.entry_time DESC LIMIT 50"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    sessions = [dict(row) for row in rows]
    return jsonify(sessions)


@app.route("/api/reports")
def api_reports():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    conn = get_db_connection()
    query = """
        SELECT ps.id, v.license_plate, v.vehicle_type, ps.entry_time,
               ps.exit_time, ps.total_fee, ps.spot_number
        FROM parking_sessions ps
        JOIN vehicles v ON ps.vehicle_id = v.id
        WHERE 1 = 1
    """
    params = []

    if start_date:
        query += " AND date(ps.entry_time) >= date(?)"
        params.append(start_date)
    if end_date:
        query += " AND date(ps.entry_time) <= date(?)"
        params.append(end_date)

    query += " ORDER BY ps.entry_time DESC"
    rows = conn.execute(query, params).fetchall()

    total_earnings = sum(row["total_fee"] or 0 for row in rows)
    sessions = [dict(row) for row in rows]

    conn.close()

    return jsonify({"total_earnings": total_earnings, "sessions": sessions})


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()
    app.run(debug=True)
