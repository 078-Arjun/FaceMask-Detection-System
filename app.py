from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import numpy as np
import cv2
from tensorflow.keras.models import load_model

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ================= LOAD MODELS =================
models = {
    "mask": load_model("models/mask_model.h5"),
    "alt": load_model("models/another_model.h5")
}

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("users.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)
    conn.close()

init_db()

# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect("/dashboard")
        else:
            return "Invalid username or password"

    return render_template("login.html")

# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            conn = sqlite3.connect("users.db")
            conn.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, password))
            conn.commit()
            conn.close()
            return redirect("/")
        except:
            return "User already exists"

    return render_template("register.html")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html")

# ================= PREDICT =================
@app.route("/predict", methods=["POST"])
def predict():
    if "user" not in session:
        return redirect("/")

    file = request.files["image"]
    model_choice = request.form["model"]

    filepath = os.path.join("static", file.filename)
    file.save(filepath)

    model = models.get(model_choice)

    img = cv2.imread(filepath)
    img = cv2.resize(img, (128, 128))
    img = img / 255.0
    img = np.reshape(img, (1, 128, 128, 3))

    pred = model.predict(img)[0][0]

    if pred < 0.5:
        label = "Mask"
        confidence = (1 - pred) * 100
    else:
        label = "No Mask"
        confidence = pred * 100

    return render_template(
        "result.html",
        label=label,
        confidence=round(confidence, 2),
        image=filepath
    )

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)