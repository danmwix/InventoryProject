@"
# InventoryProject — IT Inventory System

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

1. Open **MySQL Workbench**.
2. Click your local connection (usually named ``Local instance MySQL80`` or similar) and log in with your MySQL root password.
3. Go to **File → Open SQL Script...** and select ``schema.sql`` from the cloned project folder.
4. Click the **lightning bolt icon** (Execute) in the toolbar to run the whole script.
5. Confirm it worked: in the left sidebar under **Schemas**, right-click and **Refresh All**, then check that ``it_inventory`` appears with ``users`` and ``items`` tables inside it.

### 5. Create your own \`config.py\`

This file is **not** in the repo (it holds passwords) — you must create it yourself:

```powershell
copy config.example.py config.py
```

Open ``config.py`` and change only the ``user`` and ``password`` fields to match **your own** MySQL Workbench login:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",              # <-- your MySQL username
    "password": "your_password", # <-- your MySQL password
    "database": "it_inventory"
}
```

Leave everything else in the file (``SECRET_KEY``, ``UPLOAD_FOLDER``, ``CATEGORY_ICONS``) untouched.

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

The app binds to ``0.0.0.0``, so anyone on the same Wi-Fi/network can reach it at:

\`\`\`
http://<host-machine's-IP>:5000
\`\`\`

Find the host machine's IP with ``ipconfig`` (look for IPv4 Address).

## Day-to-day Git workflow (for the team)

```powershell
git pull                     # get latest changes before you start
# ... make your changes ...
git add .
git commit -m "describe what you changed"
git push
```

Pull before you push, and communicate in the group chat if you're editing the same file as someone else to avoid merge conflicts.

## Project structure

\`\`\`
InventoryProject/
├── app.py                  # Routes: auth, item CRUD, search, CSV export
├── auth.py                 # Signup/login/logout, password hashing, route protection
├── db.py                   # MySQL connection handling
├── config.py                # Your local DB credentials (NOT in git)
├── config.example.py       # Template — copy this to config.py
├── schema.sql               # Run this in MySQL Workbench to create the DB
├── requirements.txt
├── templates/               # HTML pages
├── static/
│   ├── style.css
│   └── uploads/             # Item photos (not tracked in git)
└── README.md
\`\`\`

## Troubleshooting

- **``Access denied for user``** → your ``config.py`` password doesn't match your MySQL login.
- **``Unknown database 'it_inventory'``** → you skipped running ``schema.sql``.
- **Port 5000 already in use** → close any other running instance of ``app.py``, or change the port in the last line of ``app.py``.
"@ | Out-File -FilePath README.md -Encoding utf8
