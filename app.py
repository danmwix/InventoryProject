# app.py
import os
import csv
import io
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from werkzeug.utils import secure_filename
from config import SECRET_KEY, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, CATEGORY_ICONS, CATEGORY_COLORS
from db import get_db_connection
from auth import create_user, verify_user, login_required

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


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
        flash("If that email exists, a reset link would be sent (not yet implemented).", "success")
        return redirect(url_for("forgot_password"))
    return render_template("forgot_password.html")


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
    """Returns just the results fragment (count + table/empty-state) for live search."""
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