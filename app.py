# app.py
import os
import csv
import io
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from werkzeug.utils import secure_filename
from config import SECRET_KEY, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, CATEGORY_ICONS, CATEGORY_COLORS
from db import get_db_connection
from auth import (
    create_user, verify_user, login_required, admin_required,
    create_reset_request, get_pending_requests, get_all_users,
    admin_reset_password, change_password
)

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    return response


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.context_processor
def inject_globals():
    return {"category_icons": CATEGORY_ICONS, "category_colors": CATEGORY_COLORS}


def fetch_items(query, category_filter):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    sql = "SELECT * FROM items WHERE 1=1"
    params = []

    if query:
        like = f"%{query}%"
        sql += " AND (serial_number LIKE %s OR model LIKE %s OR brand LIKE %s)"
        params += [like, like, like]

    if category_filter:
        sql += " AND category = %s"
        params.append(category_filter)

    sql += " ORDER BY id DESC"
    cursor.execute(sql, tuple(params))
    items = cursor.fetchall()

    cursor.close()
    conn.close()
    return items


# ---------- AUTH ROUTES ----------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not email or not password or not confirm:
            flash("All fields are required.", "error")
            return redirect(url_for("signup"))
        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for("signup"))

        success, error = create_user(email, password)
        if success:
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))
        else:
            flash(error, "error")
            return redirect(url_for("signup"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = verify_user(email, password)

        if user:
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            session["is_admin"] = bool(user.get("is_admin"))
            flash("Logged in successfully.", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("login"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if email:
            create_reset_request(email)

        # Same message either way, so this can't be used to check which emails exist.
        flash("If that email is registered, your admin has been notified and will reset your password.", "success")
        return redirect(url_for("forgot_password"))

    return render_template("forgot_password.html")


@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password_route():
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        if not current_password or not new_password or not confirm:
            flash("All fields are required.", "error")
            return redirect(url_for("change_password_route"))
        if new_password != confirm:
            flash("New passwords do not match.", "error")
            return redirect(url_for("change_password_route"))

        success, error = change_password(session["user_id"], current_password, new_password)
        if success:
            flash("Password changed successfully.", "success")
            return redirect(url_for("index"))
        else:
            flash(error, "error")
            return redirect(url_for("change_password_route"))

    return render_template("change_password.html")


# ---------- ADMIN ROUTES ----------

@app.route("/admin")
@admin_required
def admin_dashboard():
    users = get_all_users()
    pending = get_pending_requests()
    return render_template("admin_dashboard.html", users=users, pending=pending)


@app.route("/admin/reset/<int:user_id>", methods=["GET", "POST"])
@admin_required
def admin_reset(user_id):
    request_id = request.args.get("request_id", type=int)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, email FROM users WHERE id = %s", (user_id,))
    target_user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not target_user:
        flash("User not found.", "error")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        if not new_password or len(new_password) < 6:
            flash("Temporary password must be at least 6 characters.", "error")
            return redirect(url_for("admin_reset", user_id=user_id, request_id=request_id))

        admin_reset_password(user_id, new_password, request_id=request_id)
        flash(f"Password reset for {target_user['email']}. Give them the temporary password directly.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin_reset.html", target_user=target_user, request_id=request_id)


# ---------- ITEM ROUTES ----------

@app.route("/")
@login_required
def index():
    query = request.args.get("q", "").strip()
    category_filter = request.args.get("category", "").strip()

    items = fetch_items(query, category_filter)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT category, COUNT(*) AS total FROM items GROUP BY category")
    category_counts = {row["category"]: row["total"] for row in cursor.fetchall()}
    cursor.execute("SELECT COUNT(*) AS total FROM items")
    total_items = cursor.fetchone()["total"]
    cursor.close()
    conn.close()

    return render_template(
        "index.html",
        items=items,
        query=query,
        category_filter=category_filter,
        count=len(items),
        category_counts=category_counts,
        total_items=total_items
    )


@app.route("/api/search")
@login_required
def api_search():
    query = request.args.get("q", "").strip()
    category_filter = request.args.get("category", "").strip()
    items = fetch_items(query, category_filter)

    return render_template(
        "_results.html",
        items=items,
        query=query,
        category_filter=category_filter,
        count=len(items)
    )


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_item():
    if request.method == "POST":
        serial_number = request.form.get("serial_number", "").strip()
        model = request.form.get("model", "").strip()
        brand = request.form.get("brand", "").strip()
        category = request.form.get("category", "Other").strip()
        image_file = request.files.get("image")

        if not serial_number or not model or not brand:
            flash("All fields are required.", "error")
            return redirect(url_for("add_item"))

        image_path = None
        if image_file and image_file.filename and allowed_file(image_file.filename):
            filename = secure_filename(f"{serial_number}_{image_file.filename}")
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            image_path = filename

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO items (serial_number, model, brand, category, image_path) VALUES (%s, %s, %s, %s, %s)",
                (serial_number, model, brand, category, image_path)
            )
            conn.commit()
            flash("Item added.", "success")
            return redirect(url_for("index"))
        except mysql.connector.IntegrityError:
            flash(f"An item with serial number '{serial_number}' already exists.", "error")
            return redirect(url_for("add_item"))
        finally:
            cursor.close()
            conn.close()

    return render_template("form.html", item=None, categories=list(CATEGORY_ICONS.keys()))


@app.route("/edit/<int:item_id>", methods=["GET", "POST"])
@login_required
def edit_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        serial_number = request.form.get("serial_number", "").strip()
        model = request.form.get("model", "").strip()
        brand = request.form.get("brand", "").strip()
        category = request.form.get("category", "Other").strip()
        image_file = request.files.get("image")

        if not serial_number or not model or not brand:
            flash("All fields are required.", "error")
            cursor.close()
            conn.close()
            return redirect(url_for("edit_item", item_id=item_id))

        cursor.execute("SELECT image_path FROM items WHERE id = %s", (item_id,))
        existing = cursor.fetchone()
        image_path = existing["image_path"] if existing else None

        if image_file and image_file.filename and allowed_file(image_file.filename):
            filename = secure_filename(f"{serial_number}_{image_file.filename}")
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            image_path = filename

        try:
            cursor.execute(
                "UPDATE items SET serial_number=%s, model=%s, brand=%s, category=%s, image_path=%s WHERE id=%s",
                (serial_number, model, brand, category, image_path, item_id)
            )
            conn.commit()
            flash("Item updated.", "success")
            return redirect(url_for("index"))
        except mysql.connector.IntegrityError:
            flash(f"An item with serial number '{serial_number}' already exists.", "error")
            return redirect(url_for("edit_item", item_id=item_id))
        finally:
            cursor.close()
            conn.close()

    cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
    item = cursor.fetchone()
    cursor.close()
    conn.close()

    if not item:
        flash("Item not found.", "error")
        return redirect(url_for("index"))

    return render_template("form.html", item=item, categories=list(CATEGORY_ICONS.keys()))


@app.route("/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Item deleted.", "success")
    return redirect(url_for("index"))


@app.route("/export")
@login_required
def export_csv():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT serial_number, model, brand, category FROM items ORDER BY id")
    items = cursor.fetchall()
    cursor.close()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Serial Number", "Model", "Brand", "Category"])
    for item in items:
        writer.writerow([item["serial_number"], item["model"], item["brand"], item["category"]])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventory_export.csv"}
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)