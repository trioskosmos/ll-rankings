import csv
import re
import sqlite3
from pathlib import Path

def parse_song_entry(entry: str):
    if not entry or entry.strip() == "":
        return None, None
    entry = re.sub(r'^\d+\.\s*', '', entry.strip())
    parts = entry.split(' - ', 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return entry.strip(), None

def normalize_name(name: str) -> str:
    name = name.replace('\u2018', "'").replace('\u2019', "'")
    name = name.replace('\u201c', '"').replace('\u201d', '"')
    return name.strip()

conn = sqlite3.connect('api/rankings.db')
cursor = conn.cursor()

# Get all songs
cursor.execute("SELECT id, name FROM songs WHERE franchise_id = (SELECT id FROM franchises WHERE name = 'liella')")
songs = cursor.fetchall()
song_by_name = {normalize_name(name): id for id, name in songs}
# Also add exact matches
for id, name in songs:
    song_by_name[name] = id

print(f"Loaded {len(songs)} songs from DB")

# Read CSV row 4, column for Trios (Last column)
with open('api/app/seeds/user_rankings.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    rows = list(reader)

# Header: User Name,Rumi,kusa,Neptune,HooKnows,Honobruh,Dyrea,Wumbo,Coolguy,Trios
# Trios is index 9 (0-based) in rows (excluding first col) -> index 9 in row array?
# Header row: 'User Name', 'Rumi', ...
# row[9] is Trios? Check header
header = rows[0]
trios_idx = -1
for i, h in enumerate(header):
    if h.strip() == 'Trios':
        trios_idx = i
        break

print(f"Trios column index: {trios_idx}")

# Row 4 (index 3 in 0-based list)
trios_entry = rows[3][trios_idx]
print(f"Line 4 entry for Trios: '{trios_entry}'")

song_name, artist = parse_song_entry(trios_entry)
print(f"Parsed song name: '{song_name}'")

# Try to match
normalized = normalize_name(song_name)
print(f"Normalized: '{normalized}'")

if normalized in song_by_name:
    print(f"MATCH FOUND! ID: {song_by_name[normalized]}")
elif song_name in song_by_name:
    print(f"EXACT MATCH FOUND! ID: {song_by_name[song_name]}")
else:
    print("NO MATCH FOUND!")
    # Debug: Check for partial matches
    for s in song_by_name.keys():
        if "ワイルド" in s:
            print(f"  Candidate in DB: '{s}'")
            print(f"  Bytes DB: {s.encode('utf-8')}")
            print(f"  Bytes CSV: {normalized.encode('utf-8')}")

conn.close()
