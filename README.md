# InventoryProject
# IT Inventory System

A Flask web app for tracking IT assets (laptops, desktops, printers, monitors) with login, search, category filters, and photo uploads.

## Prerequisites

- Python 3.10+
- MySQL Server + MySQL Workbench
- Git

## Setup (do this once per machine)

### 1. Clone the repo

```powershell
git clone https://github.com/danmwix/InventoryProject.git
cd InventoryProject
```

### 2. Create and activate a virtual environment

```powershell
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your prompt.

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Set up the database in MySQL Workbench

- Open **MySQL Workbench** and connect to your local MySQL server.
- Open `schema.sql` (File → Open SQL Script).
- Click the **lightning bolt icon** (Execute) to run the whole script.
- This creates the `it_inventory` database with `users` and `items` tables.

### 5. Create your own `config.py`

This file is **not** in the repo (it holds passwords) — you must create it yourself:

```powershell
copy config.example.py config.py
```

Then open `config.py` and change only the `user` and `password` fields to match **your own** MySQL Workbench login:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",              # <-- your MySQL username
    "password": "your_password", # <-- your MySQL password
    "database": "it_inventory"
}
```

Leave everything else in the file (`SECRET_KEY`, `UPLOAD_FOLDER`, `CATEGORY_ICONS`) untouched.

### 6. Create the uploads folder (if missing)

```powershell
mkdir static\uploads
```

### 7. Run the app

```powershell
python app.py
```

Visit **http://127.0.0.1:5000/signup** to create your first account, then log in.

## Running on the shared network (LAN)

The app already binds to `0.0.0.0`, so anyone on the same Wi-Fi/network can reach it at:
