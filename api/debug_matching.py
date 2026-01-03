
import json
import os

# Define the target names from subgroups_new.toml
target_subgroups = [
    "Kanon Solos",
    "Keke Solos",
    "Chisato Solos",
    "Sumire Solos",
    "Ren Solos",
    "Kinako Solos",
    "Mei Solos",
    "Shiki Solos",
    "Natsumi Solos",
    "Wien Solos",
    "Tomari Solos"
]

def check_matches():
    # Load artists-info.json
    try:
        data_path = r"c:\Users\trios\.gemini\antigravity\scratch\ll-rankings\data\artists-info.json"
        with open(data_path, 'r', encoding='utf-8') as f:
            artists = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    # Build index
    group_chars = {}
    for a in artists:
        if a.get('characters'):
            group_chars[a['name']] = a['characters']
            if a.get('englishName'):
                group_chars[a['englishName']] = a['characters']

    print(f"Loaded {len(group_chars)} artist keys.")
    
    # Check each target
    for name_key in target_subgroups:
        matched_cids = None
        
        # Logic from analysis.py
        if name_key in group_chars:
            matched_cids = group_chars[name_key]
        elif name_key.endswith(" Solos"):
             base_name = name_key.replace(" Solos", "")
             # Look for artist whose English name contains base_name
             for en_name, cids in group_chars.items():
                 # Match must be len(cids) == 1 (Solo) and contain base_name
                 # BUT analysis.py logic was:
                 # for en_name, cids in group_chars.items():
                 #     if len(cids) == 1 and base_name in en_name:
                 #         matched_cids = cids; break
                 if len(cids) == 1 and base_name in en_name:
                     matched_cids = cids
                     # print(f"  Matched '{base_name}' to '{en_name}'")
                     break
        
        status = "FAIL"
        if matched_cids:
            if len(matched_cids) == 1:
                status = "OK"
            else:
                status = f"FAIL (Count {len(matched_cids)})"
        
        print(f"'{name_key}' -> {status}")

if __name__ == "__main__":
    check_matches()
