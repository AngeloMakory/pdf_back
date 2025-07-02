from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)

db = mysql.connector.connect(
    host="172.17.0.1",
    user="root",
    password="Angelo@123",
    database="pdf_db"
)
cursor = db.cursor(dictionary=True)

cursor.execute("SHOW TABLES;")
for table in cursor.fetchall():
    print(table)


@app.route("/api/messages", methods=["GET"])
def get_messages():
    cursor.execute("SELECT * FROM messages")
    messages = cursor.fetchall()
    return jsonify(messages)

@app.route("/api/messages", methods=["POST"])
def add_message():
    data = request.json
    cursor.execute("INSERT INTO messages (content) VALUES (%s)", (data["content"],))
    db.commit()
    return jsonify({"message": "Added"}), 201

if __name__ == "__main__":
    app.run(debug=True)
