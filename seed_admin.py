# seed_admin.py
from werkzeug.security import generate_password_hash
from db import get_db_connection

ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "Admin123!"


def seed_admin():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    password_hash = generate_password_hash(ADMIN_PASSWORD)

    cursor.execute("SELECT id FROM users WHERE email = %s", (ADMIN_EMAIL,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            "UPDATE users SET password_hash = %s, is_admin = 1 WHERE email = %s",
            (password_hash, ADMIN_EMAIL)
        )
        print(f"Admin account updated: {ADMIN_EMAIL}")
    else:
        cursor.execute(
            "INSERT INTO users (email, password_hash, is_admin) VALUES (%s, %s, 1)",
            (ADMIN_EMAIL, password_hash)
        )
        print(f"Admin account created: {ADMIN_EMAIL}")

    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    seed_admin()