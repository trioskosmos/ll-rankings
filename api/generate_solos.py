
import json

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_liella_solos():
    songs = load_json('../data/song-info.json')
    
    # Mapping Target Artist ID -> Subgroup Key
    # IDs verified from artists-info.json
    solo_artist_map = {
        "92": "liella.kanon_solos",
        "93": "liella.keke_solos",
        "94": "liella.chisato_solos",
        "95": "liella.sumire_solos",
        "96": "liella.ren_solos",
        "113": "liella.kinako_solos",
        "118": "liella.mei_solos",
        "119": "liella.shiki_solos",
        "117": "liella.natsumi_solos",
        "114": "liella.wien_solos"
    }
    
    # Also need maps for the Subgroup Names in TOML?
    # I'll just use the keys to group the songs, then print sections.
    # We might need to preserve the English Name if we want complete TOML.
    # Currently subgroups.toml has:
    # [liella.kanon_solos]
    # name = "Kanon Solos"
    # is_custom = false
    # is_subunit = true
    # songs = [...]
    
    subgroup_names = {
        "liella.kanon_solos": "Kanon Solos",
        "liella.keke_solos": "Keke Solos",
        "liella.chisato_solos": "Chisato Solos",
        "liella.sumire_solos": "Sumire Solos",
        "liella.ren_solos": "Ren Solos",
        "liella.kinako_solos": "Kinako Solos",
        "liella.mei_solos": "Mei Solos",
        "liella.shiki_solos": "Shiki Solos",
        "liella.natsumi_solos": "Natsumi Solos",
        "liella.wien_solos": "Wien Solos"
    }

    collected_songs = {k: [] for k in solo_artist_map.values()}
    
    for song in songs:
        if not song.get('artists'):
            continue
            
        artists = song['artists']
        # Looking for strict solo: Exactly one artist, ID matches one of our targets
        if len(artists) == 1:
            aid = artists[0]['id']
            if aid in solo_artist_map:
                key = solo_artist_map[aid]
                collected_songs[key].append(song['name'])
    
    # Output TOML
    lines = []
    for key, song_list in collected_songs.items():
        # Sort for stability?
        # song_list.sort() # Might break if verifying order, but usually safe for sets
        
        lines.append(f"[{key}]")
        lines.append(f'name = "{subgroup_names[key]}"')
        lines.append("is_custom = false")
        lines.append("is_subunit = true")
        lines.append("songs = [")
        for i, s in enumerate(song_list):
            comma = "," if i < len(song_list) - 1 else ""
            lines.append(f'    "{s}"{comma}')
        lines.append("]")
        lines.append("")
    
    with open('generated_solos.toml', 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    print("Generated to generatd_solos.toml")

if __name__ == "__main__":
    generate_liella_solos()
