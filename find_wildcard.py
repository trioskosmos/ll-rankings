import sqlite3

conn = sqlite3.connect('api/rankings.db')
cursor = conn.cursor()

# Search for ワイルドカード
cursor.execute('''
    SELECT id, name 
    FROM songs 
    WHERE franchise_id = (SELECT id FROM franchises WHERE name = 'liella')
    AND name LIKE '%ワイルド%'
''')

results = cursor.fetchall()
print(f"Found {len(results)} song(s) matching 'ワイルド':")
for song_id, name in results:
    print(f"  {name} (ID: {song_id})")

print()

# Also search for Wildcard
cursor.execute('''
    SELECT id, name 
    FROM songs 
    WHERE franchise_id = (SELECT id FROM franchises WHERE name = 'liella')
    AND (name LIKE '%Wildcard%' OR name LIKE '%ワイルド%')
''')

results = cursor.fetchall()
print(f"Total found with 'Wildcard' OR 'ワイルド': {len(results)}")
for song_id, name in results:
    print(f"  {name}")

conn.close()
