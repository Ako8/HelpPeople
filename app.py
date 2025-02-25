from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from datetime import datetime
import pytz
import pymysql
pymysql.install_as_MySQLdb()


app = Flask(__name__)

# Georgian timezone
GEORGIA_TIMEZONE = pytz.timezone('Asia/Tbilisi')

# Initialize database
def init_db():
    # Ensure the instance folder exists
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    conn = sqlite3.connect('instance/requests.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS help_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact TEXT NOT NULL,
        location TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        message TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

# Initialize the database when the app starts
init_db()

@app.route('/')
def index():
    """Home page with map for submitting help requests"""
    return render_template('index.html')

@app.route('/submit_request', methods=['POST'])
def submit_request():
    name = request.form.get('name')
    contact = request.form.get('contact')
    location = request.form.get('location')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    message = request.form.get('message')
    
    if not all([name, contact, location, latitude, longitude, message]):
        return jsonify({"status": "error", "message": "All fields are required"}), 400
    
    now = datetime.now(GEORGIA_TIMEZONE)
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    ip_address = request.remote_addr
    
    conn = sqlite3.connect('instance/requests.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO help_requests (name, contact, location, latitude, longitude, message, timestamp, ip_address)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, contact, location, latitude, longitude, message, timestamp, ip_address))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": "Help request submitted successfully"})

@app.route('/requests')
def view_requests():
    """Page to view all help requests"""
    return render_template('requests.html')

@app.route('/delete_request/<int:request_id>', methods=['DELETE'])
def delete_request(request_id):
    ip_address = request.remote_addr
    
    conn = sqlite3.connect('instance/requests.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM help_requests WHERE id = ? AND ip_address = ?', (request_id, ip_address))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    if deleted:
        return jsonify({"status": "success", "message": "Request deleted successfully"})
    else:
        return jsonify({"status": "error", "message": "Request not found or not authorized to delete"}), 403

@app.route('/api/requests')
def get_requests():
    """API endpoint to get all help requests"""
    conn = sqlite3.connect('instance/requests.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM help_requests ORDER BY timestamp DESC')
    requests = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(requests)

if __name__ == '__main__':
     app.run(host='0.0.0.0', port=5000)