from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import sqlite3, os

app = Flask(__name__)

DB = "users.db"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        firstname TEXT,
        lastname TEXT,
        email TEXT,
        address TEXT,
        filename TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("register.html")
# Step 4a: registration page (store username/password)
@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, password))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return "Username already exists. Go back and try a different username."
    conn.close()

    return redirect(url_for("details_page", username=username))


# ---------- ADD LOGIN CODE HERE ----------



# Step 4b: details page (store firstname/lastname/email/address)
@app.route("/details/<username>")
def details_page(username):
    return render_template("details.html",username=username)



# Updated details handler (uses hidden field)
@app.route("/details_save", methods=["POST"])
def details_save():
    username = request.form["username"]
    firstname = request.form["firstname"]
    lastname = request.form["lastname"]
    email = request.form["email"]
    address = request.form["address"]

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        UPDATE users
        SET firstname=?, lastname=?, email=?, address=?
        WHERE username=?
    """, (firstname, lastname, email, address, username))
    conn.commit()
    conn.close()

    return redirect(url_for("profile", username=username))
# Step 4c: display page
@app.route("/profile/<username>")
def profile(username):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT firstname, lastname, email, address, filename FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()

    if not row:
        return "User not found"

    firstname, lastname, email, address, filename = row

    word_count = None
    if filename:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                word_count = len(f.read().split())

    return render_template("profile.html",
                           username=username,
                           firstname=firstname, lastname=lastname,
                           email=email, address=address,
                           filename=filename, word_count=word_count)

# Step 4d: relogin
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "SELECT 1 FROM users WHERE username=? AND password=?",
        (username, password)
    )
    ok = c.fetchone()
    conn.close()

    if ok:
        return redirect(url_for("profile", username=username))

    return "Invalid login. Try again."


# Step 4e: upload file
@app.route("/upload/<username>", methods=["POST"])
def upload(username):
    if "file" not in request.files:
        return "No file part"

    file = request.files["file"]
    if file.filename == "":
        return "No selected file"

    # optional: enforce Limerick.txt only
    if file.filename != "Limerick.txt":
        return "Please upload Limerick.txt only."

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE users SET filename=? WHERE username=?", (file.filename, username))
    conn.commit()
    conn.close()

    return redirect(url_for("profile", username=username))

# download button
@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

