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
    
    # NEW PARAMETERS
    tolerance = request.args.get('tolerance', default=2.0, type=float)
    limit = request.args.get('limit', default=12, type=int)
    
    # Cast energy to float explicitly to avoid logic errors
    energy_raw = request.args.get('energy')
    target_energy = float(energy_raw) if energy_raw else 0.7
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database error"}), 500

    params = []
    bpm_conditions = ["(tempo BETWEEN ? AND ?)"]
    params.extend([target_bpm - tolerance, target_bpm + tolerance])

    if allow_double:
        bpm_conditions.append("(tempo BETWEEN ? AND ?)")
        params.extend([(target_bpm/2) - (tolerance/2), (target_bpm/2) + (tolerance/2)])
        if target_bpm * 2 <= 240:
            bpm_conditions.append("(tempo BETWEEN ? AND ?)")
            params.extend([(target_bpm*2) - tolerance, (target_bpm*2) + tolerance])
    
    where_clause = f"({' OR '.join(bpm_conditions)})"
    
    # Energy Filter (±0.15 range)
    where_clause += " AND (energy BETWEEN ? AND ?)"
    params.extend([target_energy - 0.15, target_energy + 0.15])

    if genre and genre != "":
        where_clause += " AND genre LIKE ?"
        params.append(f"%{genre}%")
    
    query = f"SELECT name, artists, genre, tempo, energy FROM songs WHERE {where_clause} ORDER BY RANDOM() LIMIT ?"
    params.append(limit)
    
    try:
        results = conn.execute(query, params).fetchall()
        conn.close()
        return jsonify([dict(row) for row in results])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)