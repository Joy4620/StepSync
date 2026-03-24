from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__)

def get_db_connection():
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
        return jsonify({"error": "Database connection failed"}), 500

    tolerance = 2.0
    # Logic: Grouping BPM conditions in parentheses is vital for the 'AND genre' to work
    conditions = ["(tempo BETWEEN ? AND ?)"]
    params = [target_bpm - tolerance, target_bpm + tolerance]

    if allow_double:
        # Half tempo (180 -> 90)
        conditions.append("(tempo BETWEEN ? AND ?)")
        params.extend([(target_bpm/2)-1, (target_bpm/2)+1])
        # Double tempo (90 -> 180) - only if it stays under a realistic 220 BPM
        if target_bpm * 2 <= 220:
            conditions.append("(tempo BETWEEN ? AND ?)")
            params.extend([(target_bpm*2)-2, (target_bpm*2)+2])
    
    where_bpm = " OR ".join(conditions)
    query = f"SELECT name, artists, genre, tempo FROM songs WHERE ({where_bpm})"

    if genre and genre != "":
        query += " AND genre LIKE ?"
        params.append(genre)
    
    query += " ORDER BY RANDOM() LIMIT 12"
    
    try:
        results = conn.execute(query, params).fetchall()
        conn.close()
        return jsonify([dict(row) for row in results])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)