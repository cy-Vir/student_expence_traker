from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key"


def init_db():
   
    conn = sqlite3.connect("password.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

    
    conn = sqlite3.connect("exp.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exp(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            name TEXT,
            category TEXT,
            amount REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()


def add_test_user():
    try:
        conn = sqlite3.connect("password.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users(username, password) VALUES (?, ?)", ("viraj", "admin"))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        pass 
add_test_user()


def check_user(username, password):
    conn = sqlite3.connect("password.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and user[0] == password: 
        return True
    return False

def add_user(username, password):
    try:
        conn = sqlite3.connect("password.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users(username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            return render_template("login.html", error="Enter both username and password")
        if check_user(username, password):
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            return render_template("signup.html", error="All fields are required")
        if add_user(username, password):
            return redirect(url_for("login"))
        else:
            return render_template("signup.html", error="Username already exists")
    return render_template("signup.html")

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]

    conn = sqlite3.connect("exp.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, category, amount FROM exp WHERE username=?", (username,))
    expenses = cursor.fetchall()
    cursor.execute("SELECT SUM(amount) FROM exp WHERE username=?", (username,))
    total_spent = cursor.fetchone()[0] or 0
    conn.close()

    total_budget = 10000
    remaining = total_budget - total_spent

    return render_template(
        "dashboard.html",
        username=username,
        expenses=expenses,
        total_spent=total_spent,
        remaining=remaining
    )

@app.route("/addexp", methods=["GET", "POST"])
def addexp():
    if "username" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        name = request.form.get("name")
        category = request.form.get("category")
        amount = request.form.get("amount")
        if not name or not category or not amount:
            return render_template("addexp.html", error="All fields are required")
        try:
            amount = float(amount)
        except ValueError:
            return render_template("addexp.html", error="Amount must be a number")
        conn = sqlite3.connect("exp.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO exp(username, name, category, amount) VALUES (?, ?, ?, ?)",
                       (session["username"], name, category, amount))
        conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))
    return render_template("addexp.html")

@app.route("/settings")
def settings():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("settings.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
