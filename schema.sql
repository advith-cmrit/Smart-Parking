DROP TABLE IF EXISTS parking_sessions;
DROP TABLE IF EXISTS parking_spots;
DROP TABLE IF EXISTS vehicles;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'user'))
);

CREATE TABLE vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    license_plate TEXT UNIQUE NOT NULL,
    vehicle_type TEXT NOT NULL
);

CREATE TABLE parking_spots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spot_number TEXT UNIQUE NOT NULL,
    is_occupied INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE parking_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    entry_time TEXT NOT NULL,
    exit_time TEXT,
    total_fee REAL,
    spot_number TEXT NOT NULL,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);

-- Insert some sample parking spots
INSERT INTO parking_spots (spot_number, is_occupied) VALUES
('A1', 0),
('A2', 0),
('A3', 0),
('B1', 0),
('B2', 0);
