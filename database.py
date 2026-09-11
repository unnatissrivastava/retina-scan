"""
SQLite layer for RetinaScan.
No ORM — plain sqlite3, kept intentionally simple for a project this size.
"""

import sqlite3
import json
import os
from datetime import datetime

from werkzeug.security import generate_password_hash

DB_PATH = "retina_scan.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            dob TEXT,
            gender TEXT,
            password_hash TEXT NOT NULL,
            blood_group TEXT,
            existing_conditions TEXT,
            emergency_contact TEXT,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            scan_date TEXT NOT NULL,
            image_path TEXT NOT NULL,
            result TEXT NOT NULL,
            confidence REAL NOT NULL,
            explanation TEXT,
            details TEXT,
            status TEXT NOT NULL DEFAULT 'Normal',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()

    seed_demo_data()


# ============================================================
# USERS
# ============================================================

def create_user(name, email, phone, dob, gender, password_hash):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (
            name, email, phone, dob, gender,
            password_hash, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        email,
        phone,
        dob,
        gender,
        password_hash,
        datetime.now().isoformat()
    ))

    conn.commit()
    user_id = cur.lastrowid
    conn.close()

    return user_id


def get_user_by_email(email):
    conn = get_db()

    row = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    conn.close()

    return row


def get_user_by_id(user_id):
    conn = get_db()

    row = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    conn.close()

    return row


def update_profile(
    user_id,
    name,
    phone,
    gender,
    blood_group,
    existing_conditions,
    emergency_contact
):
    conn = get_db()

    conn.execute("""
        UPDATE users
        SET
            name = ?,
            phone = ?,
            gender = ?,
            blood_group = ?,
            existing_conditions = ?,
            emergency_contact = ?
        WHERE id = ?
    """, (
        name,
        phone,
        gender,
        blood_group,
        existing_conditions,
        emergency_contact,
        user_id
    ))

    conn.commit()
    conn.close()


def update_password(user_id, new_hash):
    conn = get_db()

    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (new_hash, user_id)
    )

    conn.commit()
    conn.close()


# ============================================================
# SCANS
# ============================================================

def create_scan(
    user_id,
    image_path,
    result,
    confidence,
    explanation,
    details
):
    status = (
        "Normal"
        if result == "Healthy Retina"
        else "Requires Review"
    )

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO scans (
            user_id,
            scan_date,
            image_path,
            result,
            confidence,
            explanation,
            details,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        datetime.now().isoformat(),
        image_path,
        result,
        confidence,
        explanation,
        json.dumps(details),
        status
    ))

    conn.commit()
    scan_id = cur.lastrowid
    conn.close()

    return scan_id


def get_scans_by_user(user_id, status_filter=None):
    conn = get_db()

    if status_filter and status_filter != "All":
        rows = conn.execute("""
            SELECT *
            FROM scans
            WHERE user_id = ?
            AND status = ?
            ORDER BY scan_date DESC
        """, (
            user_id,
            status_filter
        )).fetchall()
    else:
        rows = conn.execute("""
            SELECT *
            FROM scans
            WHERE user_id = ?
            ORDER BY scan_date DESC
        """, (
            user_id,
        )).fetchall()

    conn.close()

    return rows


def get_scan_by_id(scan_id, user_id):
    conn = get_db()

    row = conn.execute("""
        SELECT *
        FROM scans
        WHERE id = ?
        AND user_id = ?
    """, (
        scan_id,
        user_id
    )).fetchone()

    conn.close()

    return row


def get_dashboard_stats(user_id):
    conn = get_db()

    total_scans = conn.execute(
        "SELECT COUNT(*) FROM scans WHERE user_id = ?",
        (user_id,)
    ).fetchone()[0]

    total_reports = total_scans

    recent = conn.execute("""
        SELECT *
        FROM scans
        WHERE user_id = ?
        ORDER BY scan_date DESC
        LIMIT 5
    """, (
        user_id,
    )).fetchall()

    conn.close()

    return {
        "total_scans": total_scans,
        "total_reports": total_reports,
        "recent": recent
    }


# ============================================================
# DEMO DATA
# ============================================================

def seed_demo_data():

    demo_email = "demo@retinascan.com"

    conn = get_db()
    cur = conn.cursor()

    # Check if demo user already exists
    existing_user = cur.execute("""
        SELECT id
        FROM users
        WHERE email = ?
    """, (demo_email,)).fetchone()

    if existing_user:
        conn.close()
        return

    # --------------------------------------------------------
    # Create demo user
    # --------------------------------------------------------

    password_hash = generate_password_hash("Demo@123")

    cur.execute("""
        INSERT INTO users (
            name,
            email,
            phone,
            dob,
            gender,
            password_hash,
            blood_group,
            existing_conditions,
            emergency_contact,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Aarav Sharma",
        demo_email,
        "+91 98765 43210",
        "1984-06-18",
        "Male",
        password_hash,
        "O+",
        "Hypertension",
        "+91 98765 43211",
        datetime.now().isoformat()
    ))

    demo_user_id = cur.lastrowid

    # --------------------------------------------------------
    # Demo image folder
    # --------------------------------------------------------

    demo_folder = os.path.join(
        "static",
        "uploads"
    )

    os.makedirs(
        demo_folder,
        exist_ok=True
    )

    demo_images = [
        "static/uploads/demo_retina_1.svg",
        "static/uploads/demo_retina_2.svg",
        "static/uploads/demo_retina_3.svg"
    ]

    # --------------------------------------------------------
    # Demo retinal image placeholders
    # --------------------------------------------------------

    svg_images = [

"""<svg xmlns="http://www.w3.org/2000/svg"
width="600" height="600" viewBox="0 0 600 600">

<rect width="600" height="600" fill="#111111"/>

<circle cx="300" cy="300" r="245" fill="#754633"/>
<circle cx="300" cy="300" r="185" fill="#a7664c"/>
<circle cx="300" cy="300" r="72" fill="#161616"/>

<circle cx="278" cy="275" r="18"
fill="#ffffff" opacity="0.55"/>

<path d="M300 300 C220 230 150 185 75 145"
stroke="#df9a78" stroke-width="9" fill="none"/>

<path d="M300 300 C380 230 450 185 525 145"
stroke="#df9a78" stroke-width="9" fill="none"/>

<path d="M300 300 C235 350 160 410 90 470"
stroke="#d68b6c" stroke-width="8" fill="none"/>

<path d="M300 300 C365 350 440 410 510 470"
stroke="#d68b6c" stroke-width="8" fill="none"/>

<path d="M300 300 C290 220 295 155 305 80"
stroke="#c9785d" stroke-width="6" fill="none"/>

</svg>""",

"""<svg xmlns="http://www.w3.org/2000/svg"
width="600" height="600" viewBox="0 0 600 600">

<rect width="600" height="600" fill="#111111"/>

<circle cx="300" cy="300" r="245" fill="#75422f"/>
<circle cx="300" cy="300" r="185" fill="#a96148"/>
<circle cx="300" cy="300" r="70" fill="#151515"/>

<circle cx="278" cy="275" r="17"
fill="#ffffff" opacity="0.5"/>

<path d="M300 300 C215 245 140 210 65 180"
stroke="#e09b79" stroke-width="10" fill="none"/>

<path d="M300 300 C390 245 465 210 535 180"
stroke="#e09b79" stroke-width="10" fill="none"/>

<path d="M300 300 C225 360 155 425 80 490"
stroke="#d27d60" stroke-width="9" fill="none"/>

<path d="M300 300 C375 360 445 425 520 490"
stroke="#d27d60" stroke-width="9" fill="none"/>

<circle cx="205" cy="245" r="8" fill="#8d3028"/>
<circle cx="420" cy="365" r="7" fill="#8d3028"/>

</svg>""",

"""<svg xmlns="http://www.w3.org/2000/svg"
width="600" height="600" viewBox="0 0 600 600">

<rect width="600" height="600" fill="#111111"/>

<circle cx="300" cy="300" r="245" fill="#754733"/>
<circle cx="300" cy="300" r="185" fill="#aa6a4e"/>
<circle cx="300" cy="300" r="70" fill="#151515"/>

<circle cx="278" cy="275" r="17"
fill="#ffffff" opacity="0.55"/>

<path d="M300 300 C215 225 140 170 65 125"
stroke="#df9a78" stroke-width="9" fill="none"/>

<path d="M300 300 C385 225 460 170 535 125"
stroke="#df9a78" stroke-width="9" fill="none"/>

<path d="M300 300 C235 360 160 425 80 495"
stroke="#d68b6c" stroke-width="8" fill="none"/>

<path d="M300 300 C365 360 440 425 520 495"
stroke="#d68b6c" stroke-width="8" fill="none"/>

</svg>"""
    ]

    for image_path, svg_content in zip(
        demo_images,
        svg_images
    ):
        full_path = image_path.replace("/", os.sep)

        if not os.path.exists(full_path):
            with open(
                full_path,
                "w",
                encoding="utf-8"
            ) as file:
                file.write(svg_content)

    # ========================================================
    # DEMO REPORT 1
    # ========================================================

    cur.execute("""
        INSERT INTO scans (
            user_id,
            scan_date,
            image_path,
            result,
            confidence,
            explanation,
            details,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        demo_user_id,
        "2026-08-12T10:30:00",
        demo_images[0],
        "Healthy Retina",
        0.94,
        "No significant signs of diabetic retinopathy were identified in the analyzed retinal image.",
        json.dumps({
            "microaneurysms": "Not detected",
            "hemorrhages": "Not detected",
            "exudates": "Not detected",
            "vessel_pattern": "Within expected range",
            "recommendation": "Continue routine eye screening."
        }),
        "Normal"
    ))

    # ========================================================
    # DEMO REPORT 2
    # ========================================================

    cur.execute("""
        INSERT INTO scans (
            user_id,
            scan_date,
            image_path,
            result,
            confidence,
            explanation,
            details,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        demo_user_id,
        "2026-07-04T14:15:00",
        demo_images[1],
        "Mild Signs Detected",
        0.81,
        "The image shows subtle retinal changes that may require clinical review.",
        json.dumps({
            "microaneurysms": "Few suspected",
            "hemorrhages": "Not clearly detected",
            "exudates": "Not detected",
            "vessel_pattern": "Minor irregularities",
            "recommendation": "Consider follow-up with an eye-care professional."
        }),
        "Requires Review"
    ))

    # ========================================================
    # DEMO REPORT 3
    # ========================================================

    cur.execute("""
        INSERT INTO scans (
            user_id,
            scan_date,
            image_path,
            result,
            confidence,
            explanation,
            details,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        demo_user_id,
        "2026-05-21T09:45:00",
        demo_images[2],
        "Healthy Retina",
        0.91,
        "The retinal image does not show significant features associated with diabetic retinopathy.",
        json.dumps({
            "microaneurysms": "Not detected",
            "hemorrhages": "Not detected",
            "exudates": "Not detected",
            "vessel_pattern": "Within expected range",
            "recommendation": "Routine screening recommended."
        }),
        "Normal"
    ))

    conn.commit()
    conn.close()