# auth.py
import mysql.connector
from functools import wraps
from flask import session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection


def create_user(email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    try:
        cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
            (email, password_hash)
        )
        conn.commit()
        return True, None
    except mysql.connector.IntegrityError:
        return False, "An account with that email already exists."
    finally:
        cursor.close()
        conn.close()


def verify_user(email, password):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and check_password_hash(user["password_hash"], password):
        return user
    return None


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        if not session.get("is_admin"):
            flash("Admin access only.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function


# ---------- ADMIN-ASSISTED PASSWORD RESET ----------

def create_reset_request(email):
    """Logs a reset request if the email belongs to a real account.
    Returns True if a request was created, False otherwise."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        return False

    cursor.execute(
        "INSERT INTO password_reset_requests (user_id, status) VALUES (%s, 'pending')",
        (user["id"],)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True


def get_pending_requests():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.id AS request_id, r.requested_at, u.id AS user_id, u.email
        FROM password_reset_requests r
        JOIN users u ON r.user_id = u.id
        WHERE r.status = 'pending'
        ORDER BY r.requested_at ASC
    """)
    requests = cursor.fetchall()
    cursor.close()
    conn.close()
    return requests


def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, email, is_admin, created_at FROM users ORDER BY email ASC")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users


def admin_reset_password(user_id, new_password, request_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = generate_password_hash(new_password)
    cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (password_hash, user_id))

    if request_id:
        cursor.execute(
            "UPDATE password_reset_requests SET status = 'resolved', resolved_at = NOW() WHERE id = %s",
            (request_id,)
        )

    conn.commit()
    cursor.close()
    conn.close()


def change_password(user_id, current_password, new_password):
    """Used by a logged-in user to change their own password."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if not user or not check_password_hash(user["password_hash"], current_password):
        cursor.close()
        conn.close()
        return False, "Current password is incorrect."

    new_hash = generate_password_hash(new_password)
    cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    return True, None