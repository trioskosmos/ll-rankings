

import json
import re

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_toml_arrays(path):
    """
    Very naive parser to extract string arrays from TOML sections.
    """
    data = {}
    current_section = None
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    in_array = False
    current_array_key = None
    current_array_values = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        # Section
        sec_match = re.match(r'^\[(.+)\]$', line)
        if sec_match:
            current_section = sec_match.group(1)
            data[current_section] = {}
            continue
            
        if current_section is None:
            continue
            
        # Key = Value
        if '=' in line and not in_array:
            parts = line.split('=', 1)
            key = parts[0].strip()
            val = parts[1].strip()
            
            if val.startswith('['):
                if val.endswith(']'):
                    # specific inline case
                    pass # logic for inline not needed for this big file usually
                else:
                    in_array = True
                    current_array_key = key
                    current_array_values = []
                    # parse first line content if any
                    content = val[1:].strip()
                    if content:
                        # naive split by comma
                        items = [x.strip().strip('"').strip("'") for x in content.split(',') if x.strip()]
                        current_array_values.extend(items)
            else:
                pass # scalar
                
        elif in_array:
            if line.endswith(']'):
                in_array = False
                content = line[:-1].strip()
                if content:
                     items = [x.strip().strip('"').strip("'") for x in content.split(',') if x.strip()]
                     current_array_values.extend(items)
                
                # filter out empty strings
                current_array_values = [x for x in current_array_values if x]
                data[current_section][current_array_key] = current_array_values
            else:
                 # content line
                 # remove trailing comma
                 clean = line.rstrip(',')
                 item = clean.strip().strip('"').strip("'")
                 if item:
                     current_array_values.append(item)

    return data

def validate_solos():
    songs = load_json('../data/song-info.json')
    artists = load_json('../data/artists-info.json')
    # Manually parse for robustness
    subgroups = parse_toml_arrays('app/seeds/subgroups.toml')

    song_map = {s['name']: s for s in songs}
    artist_map = {a['id']: a for a in artists}

    target_map = {
        'liella.kanon_solos': 37,
        'liella.keke_solos': 38,
        'liella.chisato_solos': 39,
        'liella.sumire_solos': 40,
        'liella.ren_solos': 41,
        'liella.kinako_solos': 42,
        'liella.mei_solos': 43,
        'liella.shiki_solos': 44,
        'liella.natsumi_solos': 45,
        'liella.wien_solos': 48,
        'liella.tomari_solos': 49, # Assuming validation logic check later if needed
    }

    issues = []

    for key, char_id in target_map.items():
        if key not in subgroups:
            # Maybe I defined the key wrong or it doesn't exist?
            continue
            
        data = subgroups[key]
        target_char_id = str(char_id)
        song_names = data.get('songs', [])
        
        print(f"Checking {key} (Target Char {target_char_id})...")
        
        for name in song_names:
            if name not in song_map:
                issues.append(f"[{key}] Song '{name}' not found in song-info.json")
                continue
                
            song = song_map[name]
            song_artists = song.get('artists', [])
            
            # Validity check:
            # We want to find AT LEAST ONE artist on the track that matches the criteria:
            # "The artist is composed ONLY of the target character"
            # If so, it's a valid solo track for that character's list?
            # Or must ALL artists on the track be that character?
            # Usually strict solo = 1 artist entry, and that artist entry = [char_id]
            
            is_valid = False
            found_mismatch_reason = []
            
            for sa in song_artists:
                aid = sa['id']
                if aid not in artist_map:
                    found_mismatch_reason.append(f"Artist {aid} missing")
                    continue
                
                artist_info = artist_map[aid]
                chars = artist_info.get('characters', [])
                chars = [str(c) for c in chars if c is not None]
                
                if len(chars) == 1 and chars[0] == target_char_id:
                    is_valid = True
                    break # Found the solo artist credit
                else:
                    found_mismatch_reason.append(str(chars))
            
            if not is_valid:
                 issues.append(f"[{key}] INVALID: '{name}' (Artists: {found_mismatch_reason}). Expected ['{target_char_id}']")
    
    if not issues:
        with open('validation_results.txt', 'w', encoding='utf-8') as f:
            f.write("No issues found!")
    else:
        with open('validation_results.txt', 'w', encoding='utf-8') as f:
            for i in issues:
                f.write(i + '\n')
    print("Validation complete. Check validation_results.txt")

if __name__ == "__main__":
    validate_solos()
