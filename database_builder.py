import pandas as pd
import sqlite3
import os

# Create data directory if it doesn't exist
if not os.path.exists('data'):
    os.makedirs('data')

def build_db():
    print("Reading CSV... this may take a minute due to file size.")
    # Path to your downloaded Kaggle file
    csv_path = 'data/songs.csv'
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found. Please place the Kaggle CSV in the data/ folder.")
        return

    # Load only the columns we need to save memory
    cols = ['name', 'artists', 'genre', 'tempo', 'id']
    df = pd.read_csv(csv_path, usecols=cols)

    # Clean up any missing values
    df = df.dropna(subset=['tempo'])

    print("Connecting to SQLite and writing data...")
    conn = sqlite3.connect('music_database.db')
    
    # Write to a table named 'songs'
    df.to_sql('songs', conn, if_exists='replace', index=False)
    
    # CRITICAL: Create an index on 'tempo' so searches are instant
    conn.execute("CREATE INDEX idx_tempo ON songs(tempo)")
    
    conn.close()
    print("Database built and indexed successfully!")

if __name__ == "__main__":
    build_db()