import sqlite3
import json

conn = sqlite3.connect('api/rankings.db')
c = conn.cursor()

# Check subgroup song_ids  
c.execute("SELECT name, song_ids FROM subgroups WHERE name = 'All Songs' LIMIT 1")
row = c.fetchone()
if row:
    print('Subgroup:', row[0])
    song_ids = json.loads(row[1]) if isinstance(row[1], str) else row[1]
    print('song_ids count:', len(song_ids) if song_ids else 0)
    print('song_ids sample:', song_ids[:2] if song_ids else 'EMPTY')

# Check submission parsed_rankings
c.execute("SELECT username, parsed_rankings FROM submissions WHERE username IN ('Rumi', 'kusa') LIMIT 2")
for row in c.fetchall():
    print('User:', row[0])
    rankings = json.loads(row[1]) if isinstance(row[1], str) else row[1]
    if rankings:
        sample = list(rankings.items())[:2]
        print('  parsed_rankings sample:', sample)

conn.close()
