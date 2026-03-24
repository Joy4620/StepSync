from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('music_database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate-spm', methods=['POST'])
def calculate_spm():
    data = request.json
    height = float(data.get('height', 170))  # in cm
    activity = data.get('activity', 'walk')  # walk, jog, run
    
    # Basic biomechanical estimation:
    # Taller people have longer strides, thus lower frequency (SPM) for the same speed.
    # Base SPM for a 170cm person:
    # Walk: ~115, Jog: ~145, Run: ~170
    
    if activity == 'walk':
        base_spm = 115
    elif activity == 'jog':
        base_spm = 145
    else:  # run
        base_spm = 175

    # Adjust based on height: ~1% change in SPM for every 2cm away from 170cm
    # If taller, SPM decreases. If shorter, SPM increases.
    height_diff = height - 170
    adjustment = (height_diff / 2) * 0.01
    final_spm = base_spm * (1 - adjustment)
    
    return jsonify({'spm': round(final_spm)})

@app.route('/sync', methods=['GET'])
def sync():
    target_bpm = request.args.get('target', default=120, type=float)
    genre = request.args.get('genre', default=None)
    allow_double = request.args.get('double', default='false') == 'true'
    
    # We use a 2 BPM window for CadenceSync
    tolerance = 2.0
    conn = get_db_connection()
    query = "SELECT name, artists, genre, tempo FROM songs WHERE tempo BETWEEN ? AND ?"
    params = [target_bpm - tolerance, target_bpm + tolerance]

    if allow_double:
            half_target = target_bpm / 2
            double_target = target_bpm * 2
            
            query = query[:-1]  # Remove the closing parenthesis
            query += " OR (tempo BETWEEN ? AND ?) OR (tempo BETWEEN ? AND ?))"
            params.extend([half_target - (tolerance/2), half_target + (tolerance/2)])
            params.extend([double_target - (tolerance*2), double_target + (tolerance*2)])
    else:
        # If not double, just ensure the parenthesis is closed correctly
        query += ")"

    if genre:
        query += " AND genre = ?"
        params.append(genre)
    
    query += " ORDER BY RANDOM() LIMIT 15"
    results = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(row) for row in results])

if __name__ == '__main__':
    app.run(debug=True)