import json

with open('song-info.json') as f:
    data = json.load(f)
    #print(json.dump(f, indent=4))
    f.close()


hasu = [{'name': song['name'], 'youtube_url': None} for song in data if 6 in song['seriesIds']]


with open("hasunosora.json", "w") as outfile:
    json.dump(hasu, outfile, indent=4, ensure_ascii=False)
    outfile.close()