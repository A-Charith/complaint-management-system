import sqlite3
from werkzeug.security import generate_password_hash
import os

DB = 'complaints.db'

if os.path.exists(DB):
    print(f"{DB} already exists. Remove it if you want to recreate.")
else:
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'citizen',
        region TEXT
    );
    ''')
    c.execute('''
    CREATE TABLE complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        department TEXT,
        region TEXT,
        description TEXT,
        status TEXT DEFAULT 'Pending',
        date_submitted TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    ''')
    # create default admin: email admin@example.com / password: Admin@123
    admin_pass = generate_password_hash("Admin@123")
    c.execute('''
    INSERT INTO users (name, email, password, role, region)
    VALUES (?, ?, ?, 'admin', ?)
    ''', ("Admin", "admin@example.com", admin_pass, "Head Office"))
    conn.commit()
    conn.close()
    print(f"Database {DB} created with default admin: admin@example.com / password: Admin@123")
