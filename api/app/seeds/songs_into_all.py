import json

def song_list(franchise: str) -> list:
    with open(f"{franchise}_songs.json") as f:
        data = json.load(f)
        #print(json.dump(f, indent=4))
        f.close()

    return [song['name'] for song in data]

print(song_list('aqours'))