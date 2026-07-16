@"
# InventoryProject — IT Inventory System

A Flask web application for managing IT assets such as laptops, desktops, printers, and monitors. The system includes user authentication, inventory management (CRUD), live search functionality, category filtering, image uploads, CSV export, and admin-assisted password resets.

---

## Prerequisites

Before running the project, install the following:

- Python 3.10 or newer
- MySQL Server
- MySQL Workbench
- Git

---

# Setup (Run Once Per Machine)

## 1. Clone the repository

```powershell
git clone https://github.com/danmwix/InventoryProject.git
cd InventoryProject
```

---

## 2. Create and activate a virtual environment

```powershell
python -m venv venv
venv\Scripts\activate
```

When activated, your terminal should display:

```text
(venv)
```

---

## 3. Install the project dependencies

```powershell
pip install -r requirements.txt
```

---

## 4. Create the database

1. Open **MySQL Workbench**.
2. Connect to your local MySQL server.
3. Select **File → Open SQL Script...**
4. Open the project's **schema.sql** file.
5. Click the **⚡ Execute** button.
6. Refresh the **Schemas** panel.

You should now have:

```text
it_inventory
├── users
├── items
└── password_reset_requests
```

---

## 5. Create your own config.py

For security reasons, **config.py is NOT stored in GitHub**.

Create it from the template:

```powershell
copy config.example.py config.py
```

Open **config.py** and update only your MySQL username and password.

Example:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_mysql_password",
    "database": "it_inventory"
}
```

Leave the remaining settings unchanged.

---

## 6. Create the uploads folder (if it doesn't exist)

```powershell
mkdir static\uploads
```

---

## 7. Create the admin account

Run this once — it seeds the built-in administrator login:

```powershell
python seed_admin.py
```

You should see `Admin account created: admin@gmail.com` printed in the terminal.

---

## 8. Run the application

```powershell
python app.py
```

Open your browser and visit:

http://127.0.0.1:5000/signup

Create your account, then log in.

---

# Admin Login

The system has one built-in administrator account, created by `seed_admin.py`:

```text
Email:    admin@gmail.com
Password: Admin123!
```

Log in with these credentials directly at `/login` to unlock the **Admin** link in the navbar. Keep these within the team only.

---

# How Password Resets Work

There is no email server involved. Resets are handled directly by the admin:

1. A user who forgot their password clicks **Forgot password?** on the login page and submits their email. This creates a pending request — nothing is emailed.
2. The **admin** logs in using the credentials above and opens **Admin** from the navbar.
3. Under **Pending Reset Requests**, the admin clicks **Reset Password** next to that user, enters a temporary password, and submits.
4. The admin tells the user that temporary password directly (in person, group chat, etc.).
5. The user logs in with the temporary password, then visits **Change Password** in the navbar to set their own permanent one.

The admin can also reset any user's password anytime from the **All Users** table on the Admin page, even without a pending request.

---

# Running on a Local Network (LAN)

The application runs on:

```python
host="0.0.0.0"
```

Anyone connected to the same Wi-Fi or LAN can access it using:

```text
http://<HOST-IP>:5000
```

Find your computer's IP address by running:

```powershell
ipconfig
```

Look for the **IPv4 Address**.

Example:

```text
IPv4 Address . . . . . . : 192.168.1.25
```

Your teammates would then visit:

```text
http://192.168.1.25:5000
```

---

# Daily Git Workflow

Always pull before starting work.

```powershell
git pull

# Make your changes

git add .
git commit -m "Describe your changes"
git push
```

If two people edit the same file, communicate before pushing to avoid merge conflicts.

---

# Project Structure

```text
InventoryProject/
│
├── app.py                     # Main Flask application
├── auth.py                    # Authentication + admin reset logic
├── db.py                      # Database connection helper
├── seed_admin.py               # Run once to create the admin@gmail.com account
├── schema.sql                 # MySQL database schema
├── requirements.txt           # Python dependencies
│
├── config.example.py          # Configuration template
├── config.py                  # Local credentials (ignored by Git)
│
├── README.md
├── .gitignore
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── signup.html
│   ├── forgot_password.html
│   ├── change_password.html
│   ├── admin_dashboard.html
│   ├── admin_reset.html
│   ├── index.html
│   ├── form.html
│   └── _results.html
│
├── static/
│   ├── style.css
│   └── uploads/               # Uploaded inventory images
│
└── venv/                      # Virtual environment (ignored by Git)
```

---

# Troubleshooting

### Access denied for user

Your MySQL username or password in **config.py** is incorrect.

---

### Unknown database 'it_inventory'

You have not executed **schema.sql** in MySQL Workbench.

---

### Can't log in as admin

You have not run:

```powershell
python seed_admin.py
```

---

### ModuleNotFoundError

Activate the virtual environment and reinstall the dependencies:

```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

---

### Port 5000 already in use

Close the other running Flask application or change the port in **app.py**.

---

### Images are not uploading

Ensure the folder below exists:

```text
static/
└── uploads/
```

---

### TemplateNotFound

A template listed under **Project Structure** above is missing from your local `templates/` folder. Check the list and create whichever file is missing.

---

### Git push rejected

Always pull the latest changes first:

```powershell
git pull
git push
```

If a merge conflict occurs, resolve it locally before pushing.

"@ | Out-File -FilePath README.md -Encoding utf8
