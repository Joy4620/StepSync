from flask import Flask, render_template, request, jsonify
import sqlite3
import os

# Initialize the Flask application
app = Flask(__name__)

def get_db_connection():
    """
    Establishes a connection to the SQLite database.
    Checks if the file exists first to prevent silent failures.
    """
    if not os.path.exists('music_database.db'):
        return None
    try:
        conn = sqlite3.connect('music_database.db')
        # row_factory allows us to access columns by name (like a dictionary) 
        # instead of just by index number
        conn.row_factory = sqlite3.Row
        return conn
    except:
        return None

@app.route('/')
def index():
    """Serves the main dashboard page."""
    return render_template('index.html')

@app.route('/sync', methods=['GET'])
def sync():
    """
    The main API endpoint for music synchronization.
    Takes target BPM, genre, and double-tempo preferences from the URL.
    """
    # Extract query parameters from the URL request
    target_bpm = request.args.get('target', default=120, type=float)
    genre = request.args.get('genre', default=None)
    # Convert the string 'true'/'false' from JS into a Python boolean
    allow_double = request.args.get('double', default='false') == 'true'
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database file not found. Please run database_builder.py"}), 500

    # Tolerance provides a +/- 2 BPM buffer for a more flexible search
    tolerance = 2.0
    
    # Start building the dynamic SQL query
    # We use '?' as placeholders to prevent SQL Injection attacks
    bpm_conditions = ["(tempo BETWEEN ? AND ?)"]
    params = [target_bpm - tolerance, target_bpm + tolerance]

    if allow_double:
        # Half tempo range: Matches songs where 1 beat of music = 2 steps
        bpm_conditions.append("(tempo BETWEEN ? AND ?)")
        params.extend([(target_bpm/2) - 1, (target_bpm/2) + 1])
        
        # Double tempo range: Matches songs where 2 beats of music = 1 step
        # Capped at 240 BPM as most music doesn't exceed this realistically
        if target_bpm * 2 <= 240:
            bpm_conditions.append("(tempo BETWEEN ? AND ?)")
            params.extend([(target_bpm*2) - 3, (target_bpm*2) + 3])
    
    # Combine the BPM ranges into a single string joined by 'OR'
    where_clause = " OR ".join(bpm_conditions)
    query = f"SELECT name, artists, genre, tempo FROM songs WHERE ({where_clause})"

    # If a specific genre was requested, append it to the SQL query
    if genre and genre != "":
        # 'LIKE' with '%' allows for partial matches and is usually case-insensitive
        query += " AND genre LIKE ?"
        params.append(f"%{genre}%") 
    
    # Randomize results so the user gets a fresh playlist every time
    query += " ORDER BY RANDOM() LIMIT 12"
    
    try:
        # Execute the query with the safely prepared params list
        results = conn.execute(query, params).fetchall()
        conn.close()
        # Convert the SQL rows into a standard Python list of dictionaries for JSON output
        return jsonify([dict(row) for row in results])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Start the local development server
    app.run(debug=True)