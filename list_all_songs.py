import sqlite3

conn = sqlite3.connect('api/rankings.db')
cursor = conn.cursor()

# Get all Liella songs
cursor.execute('''
    SELECT name 
    FROM songs 
    WHERE franchise_id = (SELECT id FROM franchises WHERE name = 'liella')
    ORDER BY name
''')

all_songs = [row[0] for row in cursor.fetchall()]
print(f"Total Liella songs in database: {len(all_songs)}")
print("\nAll songs:")
for i, song in enumerate(all_songs, 1):
    print(f"{i}. {song}")

conn.close()
