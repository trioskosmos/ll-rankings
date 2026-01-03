
import re
import json
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import Franchise, Subgroup, Song  # Ensure all models are imported

# Configure logging to see what's happening
logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def force_update():
    print("Starting force update...")
    
    # 1. Parse TOML manually
    toml_path = Path('app/seeds/subgroups.toml')
    if not toml_path.exists():
        print("TOML not found")
        return

    liella_config = {}
    
    current_section = None
    with open(toml_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    in_array = False
    current_array_key = None
    current_array_values = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        sec_match = re.match(r'^\[(.+)\]$', line)
        if sec_match:
            current_section = sec_match.group(1)
            # Only care about liella solos
            if current_section.startswith('liella.'):
                liella_config[current_section] = {}
            continue
            
        if current_section and current_section.startswith('liella.'):
            if '=' in line and not in_array:
                parts = line.split('=', 1)
                key = parts[0].strip()
                val = parts[1].strip()
                
                if val.startswith('['):
                    if val.endswith(']'):
                         pass # inline empty or simple
                    else:
                        in_array = True
                        current_array_key = key
                        current_array_values = []
                        content = val[1:].strip()
                        if content:
                             items = [x.strip().strip('"').strip("'") for x in content.split(',') if x.strip()]
                             current_array_values.extend(items)
                else:
                    liella_config[current_section][key] = val.strip('"').strip("'")

            elif in_array:
                if line.endswith(']'):
                    in_array = False
                    content = line[:-1].strip()
                    if content:
                         items = [x.strip().strip('"').strip("'") for x in content.split(',') if x.strip()]
                         current_array_values.extend(items)
                    liella_config[current_section][current_array_key] = current_array_values
                else:
                     clean = line.rstrip(',')
                     item = clean.strip().strip('"').strip("'")
                     if item:
                         current_array_values.append(item)
    
    # 2. DB Connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get Franchise ID
        franchise = db.query(Franchise).filter(Franchise.name == 'liella').first()
        if not franchise:
            print("Franchise not found")
            return
        fid = franchise.id
        
        # Get All Songs map
        songs = db.query(Song).filter(Song.franchise_id == fid).all()
        song_map = {s.name: str(s.id) for s in songs} 
        
        target_keys = [
            "liella.kanon_solos", "liella.keke_solos", "liella.chisato_solos",
            "liella.sumire_solos", "liella.ren_solos", "liella.kinako_solos",
            "liella.mei_solos", "liella.shiki_solos", "liella.natsumi_solos",
            "liella.wien_solos"
        ]
        
        for key in target_keys:
            if key not in liella_config:
                print(f"Key {key} not in TOML, skipping")
                continue
                
            sub_cfg = liella_config[key]
            name = sub_cfg.get('name')
            song_names = sub_cfg.get('songs', [])
            
            if not name:
                print(f"Skipping {key} (no name)")
                continue

            # Resolve IDs
            song_ids = []
            missing = []
            for sn in song_names:
                if sn in song_map:
                    song_ids.append(song_map[sn])
                else:
                    missing.append(sn)
            
            if missing:
                print(f"[{name}] Warning: Missing songs in DB: {missing}")
            
            # Find Subgroup Object
            sub = db.query(Subgroup).filter(Subgroup.name == name, Subgroup.franchise_id == fid).first()
            if sub:
                old_len = len(sub.song_ids) if sub.song_ids else 0
                print(f"Updating '{name}': {old_len} -> {len(song_ids)} songs")
                # Assign new list. SQLAlchemy JSON type should handle list->json
                sub.song_ids = song_ids
            else:
                 print(f"Subgroup '{name}' not found.")

        db.commit()
        print("Update committed.")
        
        # Clear Cache
        db.execute(text("DELETE FROM analysis_results WHERE franchise_id = :fid"), {"fid": fid})
        db.commit()
        print("Analysis cache cleared.")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    force_update()
