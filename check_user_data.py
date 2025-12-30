import sqlite3
import json

conn = sqlite3.connect('api/rankings.db')
cursor = conn.cursor()

# Get all submissions for liella
cursor.execute('''
    SELECT username, parsed_rankings 
    FROM submissions 
    WHERE franchise_id = (SELECT id FROM franchises WHERE name = 'liella')
    AND submission_status = 'VALID'
''')

rows = cursor.fetchall()
print(f"Total users: {len(rows)}\n")

for username, parsed_rankings_json in rows:
    if parsed_rankings_json:
        rankings = json.loads(parsed_rankings_json)
        print(f"{username}: {len(rankings)} songs")
        
        # Check for missing songs by getting song names
        cursor.execute('''
            SELECT id, name 
            FROM songs 
            WHERE franchise_id = (SELECT id FROM franchises WHERE name = 'liella')
        ''')
        all_songs = {str(row[0]): row[1] for row in cursor.fetchall()}
        
        ranked_song_ids = set(rankings.keys())
        all_song_ids = set(all_songs.keys())
        
        missing = all_song_ids - ranked_song_ids
        if missing:
            print(f"  Missing {len(missing)} songs:")
            for song_id in list(missing)[:5]:  # Show first 5
                print(f"    - {all_songs[song_id]}")
        print()

conn.close()
