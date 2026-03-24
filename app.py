from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__)

def get_db_connection():
    if not os.path.exists('music_database.db'):
        return None
    try:
        conn = sqlite3.connect('music_database.db')
        conn.row_factory = sqlite3.Row
        return conn
    except:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sync', methods=['GET'])
def sync():
    target_bpm = request.args.get('target', default=120, type=float)
    genre = request.args.get('genre', default=None)
    allow_double = request.args.get('double', default='false') == 'true'
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database file not found. Please run database_builder.py"}), 500

    tolerance = 2.0
    # We build a list of possible BPM ranges
    bpm_conditions = ["(tempo BETWEEN ? AND ?)"]
    params = [target_bpm - tolerance, target_bpm + tolerance]

    if allow_double:
        # Half tempo range
        bpm_conditions.append("(tempo BETWEEN ? AND ?)")
        params.extend([(target_bpm/2) - 1, (target_bpm/2) + 1])
        
        # Double tempo range (only if realistic)
        if target_bpm * 2 <= 240:
            bpm_conditions.append("(tempo BETWEEN ? AND ?)")
            params.extend([(target_bpm*2) - 3, (target_bpm*2) + 3])
    
    # Join BPM ranges with OR and wrap in parentheses
    where_clause = " OR ".join(bpm_conditions)
    query = f"SELECT name, artists, genre, tempo FROM songs WHERE ({where_clause})"

    # Add Genre filter with LIKE for case-insensitivity
    if genre and genre != "":
        query += " AND genre LIKE ?"
        params.append(f"%{genre}%") # Matches even if genre is a partial string
    
    query += " ORDER BY RANDOM() LIMIT 12"
    
    try:
        results = conn.execute(query, params).fetchall()
        conn.close()
        return jsonify([dict(row) for row in results])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)