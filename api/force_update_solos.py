
import re
import tomllib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from app.config import settings
from pathlib import Path

def force_update():
    # 1. Load TOML
    toml_path = Path('app/seeds/subgroups.toml')
    if not toml_path.exists():
        print("TOML not found")
        return

    # Manual Parser
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
                         # inline
                         pass
                    else:
                        in_array = True
                        current_array_key = key
                        current_array_values = []
                        content = val[1:].strip()
                        if content:
                             items = [x.strip().strip('"').strip("'") for x in content.split(',') if x.strip()]
                             current_array_values.extend(items)
                else:
                    # scalar
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
        fid_row = db.execute(text("SELECT id FROM franchises WHERE name='liella'")).fetchone()
        if not fid_row:
            print("Franchise not found")
            return
        fid = fid_row[0]
        
        # Get All Songs map
        songs = db.execute(text("SELECT id, name FROM songs WHERE franchise_id=:fid"), {"fid": fid}).fetchall()
        song_map = {s[1]: str(s[0]) for s in songs} # Name -> UUID string
        
        # 3. Iterate and Update
        target_keys = [
            "liella.kanon_solos", "liella.keke_solos", "liella.chisato_solos",
            "liella.sumire_solos", "liella.ren_solos", "liella.kinako_solos",
            "liella.mei_solos", "liella.shiki_solos", "liella.natsumi_solos",
            "liella.wien_solos"
        ]
        
        # ORM Update
        from app.models import Subgroup
        
        for key in target_keys:
            if key not in liella_config:
                print(f"Key {key} not in TOML, skipping")
                continue
                
            sub_cfg = liella_config[key]
            name = sub_cfg['name']
            song_names = sub_cfg['songs']
            
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
                print(f"Updating '{name}' from {len(sub.song_ids or [])} to {len(song_ids)} songs...")
                sub.song_ids = song_ids
                # Mark dirty? ORM should handle it.
            else:
                 print(f"Subgroup '{name}' not found.")

        db.commit()
        print("Update committed.")
        
        # Clear Cache
        db.execute(text("DELETE FROM analysis_results WHERE franchise_id = :fid"), {"fid": fid})
        db.commit()
        print("Analysis cache cleared.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    force_update()
