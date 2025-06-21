from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Upload folders
UPLOAD_FOLDER = "uploads"
AVATAR_FOLDER = os.path.join(UPLOAD_FOLDER, "avatars")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AVATAR_FOLDER, exist_ok=True)

# Initialize database
def init_db():
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            is_file INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

# Register
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user (username, email, password, description) VALUES (?, ?, ?, ?)",
                   (data["username"], data["email"], data["password"], data.get("description", "")))
    conn.commit()
    conn.close()
    return jsonify({"message": "Registered successfully"})

# Login
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE username=? AND password=?", (data["username"], data["password"]))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({"message": "Login successful"})
    return jsonify({"error": "Invalid credentials"}), 401

# Get all users except self
@app.route("/users")
def get_users():
    current_user = request.args.get("current_user")
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM user WHERE username != ?", (current_user,))
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(users)

# Send message
@app.route("/send", methods=["POST"])
def send():
    data = request.get_json()
    sender = data.get("sender")
    recipient = data.get("recipient")
    message = data.get("message")
    is_file = 1 if data.get("is_file") else 0
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not sender or not recipient or not message:
        return jsonify({"error": "Missing required fields"}), 400

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO messages (sender, recipient, message, timestamp, is_file)
        VALUES (?, ?, ?, ?, ?)
    """, (sender, recipient, message, timestamp, is_file))
    conn.commit()
    conn.close()

    return jsonify({"message": "Sent"})

# Get messages between users
@app.route("/messages/<sender>/<recipient>")
def get_messages(sender, recipient):
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sender, recipient, message, timestamp, is_file FROM messages
        WHERE (sender=? AND recipient=?) OR (sender=? AND recipient=?)
        ORDER BY timestamp
    """, (sender, recipient, recipient, sender))
    rows = cursor.fetchall()
    conn.close()
    messages = [
        {"sender": row[0], "recipient": row[1], "message": row[2], "timestamp": row[3], "is_file": bool(row[4])}
        for row in rows
    ]
    return jsonify(messages)

# Upload file (💡 UPDATED to use dynamic base URL)
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)
    base_url = request.host_url.rstrip('/')
    return jsonify({"file_url": f"{base_url}/uploads/{file.filename}"})

# Serve uploaded file
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Upload avatar
@app.route("/upload_avatar", methods=["POST"])
def upload_avatar():
    file = request.files["avatar"]
    username = request.form.get("username")
    if not username:
        return jsonify({"error": "Missing username"}), 400
    path = os.path.join(AVATAR_FOLDER, f"{username}.jpg")
    file.save(path)
    return jsonify({"message": "Avatar uploaded"})

# Serve avatar
@app.route("/uploads/avatars/<filename>")
def get_avatar(filename):
    return send_from_directory(AVATAR_FOLDER, filename)

# Get user info
@app.route("/userinfo")
def userinfo():
    username = request.args.get("username")
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT email, description FROM user WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify({"email": row[0], "description": row[1]})
    return jsonify({"error": "User not found"}), 404

# Update description
@app.route("/update_description", methods=["POST"])
def update_description():
    data = request.get_json()
    username = data.get("username")
    description = data.get("description")

    if not username or description is None:
        return jsonify({"error": "Missing data"}), 400

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE user SET description = ? WHERE username = ?", (description, username))
    conn.commit()
    conn.close()

    return jsonify({"message": "Description updated!"})

# List all users with description
@app.route("/all_users")
def all_users():
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, description FROM user")
    users = [{"username": row[0], "description": row[1]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(users)

# Initialize DB and run app
if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(host="0.0.0.0", port=5000)
@app.route("/")
def home():
    return "🎉 Nextalk Flask backend is live!"
