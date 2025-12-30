import sqlite3
import json

conn = sqlite3.connect('api/rankings.db')
cursor = conn.cursor()

# Get all Liella songs
cursor.execute('''
    SELECT id, name 
    FROM songs 
    WHERE franchise_id = (SELECT id FROM franchises WHERE name = 'liella')
    ORDER BY name
''')
all_songs = {str(row[0]): row[1] for row in cursor.fetchall()}
print(f"Total Liella songs in database: {len(all_songs)}\n")

# Get a sample user's rankings
cursor.execute('''
    SELECT username, parsed_rankings 
    FROM submissions 
    WHERE franchise_id = (SELECT id FROM franchises WHERE name = 'liella')
    AND submission_status = 'VALID'
    LIMIT 1
''')

row = cursor.fetchone()
if row:
    username, parsed_rankings_json = row
    rankings = json.loads(parsed_rankings_json)
    
    ranked_song_ids = set(rankings.keys())
    all_song_ids = set(all_songs.keys())
    
    missing = all_song_ids - ranked_song_ids
    
    print(f"{username} has {len(rankings)} songs ranked")
    print(f"Missing {len(missing)} song(s):\n")
    
    for song_id in sorted(missing):
        print(f"  🎵 {all_songs[song_id]}")

conn.close()
