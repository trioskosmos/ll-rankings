import urllib.request, json, time

# Wait for server
for _ in range(5):
    try:
        urllib.request.urlopen('http://localhost:8000/api/v1/subgroups?franchise=liella')
        break
    except:
        time.sleep(2)

# Get rankings
r = urllib.request.urlopen('http://localhost:8000/api/v1/analysis/rankings?franchise=liella&subgroup=All%20Songs')
data = json.loads(r.read())
rankings = data.get('rankings', [])
ranked_names = {s['song_name'] for s in rankings}

# Get all songs in subgroup
r2 = urllib.request.urlopen('http://localhost:8000/api/v1/subgroups?franchise=liella')
subgroups = json.loads(r2.read())
all_songs_sg = [sg for sg in subgroups if sg['name'] == 'All Songs'][0]

# Get all songs from API to match names
r3 = urllib.request.urlopen('http://localhost:8000/api/v1/songs?franchise=liella')
all_liella_songs = json.loads(r3.read())
id_to_name = {s['id']: s['name'] for s in all_liella_songs}

subgroup_names = {id_to_name.get(sid, sid) for sid in all_songs_sg['song_ids']}

missing = subgroup_names - ranked_names
print('Songs in subgroup but NOT in rankings:', missing)
print('Rankings count:', len(rankings))
print('Subgroup count:', len(subgroup_names))
print('Total ranked names sample:', list(ranked_names)[:5])
