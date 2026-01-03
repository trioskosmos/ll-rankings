import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from app.config import settings
from app.models import Subgroup, Song, Franchise

def debug_all_solos():
    print("DEBUG: Processing ALL Liella Solos...")


    target_keys = [
        ("liella.kanon_solos", "Kanon Solos"),
        ("liella.keke_solos", "Keke Solos"),
        ("liella.chisato_solos", "Chisato Solos"),
        ("liella.sumire_solos", "Sumire Solos"),
        ("liella.ren_solos", "Ren Solos"),
        ("liella.kinako_solos", "Kinako Solos"),
        ("liella.mei_solos", "Mei Solos"),
        ("liella.shiki_solos", "Shiki Solos"),
        ("liella.natsumi_solos", "Natsumi Solos"),
        ("liella.wien_solos", "Wien Solos")
    ]
    
    # 1. Parse All
    config = {}
    with open('app/seeds/subgroups.toml', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    current_key = None
    in_array = False
    
    for line in lines:
        line = line.strip()
        m = re.match(r'^\[(.+)\]$', line)
        if m:
            current_key = m.group(1)
            config[current_key] = []
            in_array = False
            continue
            
        if current_key and line.startswith('songs = ['):
            in_array = True
            continue
            
        if in_array:
            if line.endswith(']'):
                in_array = False
                continue
            clean = line.rstrip(',')
            clean = clean.strip('"').strip("'")
            if clean:
                config[current_key].append(clean)

    # 2. DB Update
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        franchise = db.query(Franchise).filter_by(name='liella').first()
        songs = db.query(Song).filter_by(franchise_id=franchise.id).all()
        song_map = {s.name: str(s.id) for s in songs}
        
        for key, name in target_keys:
            if key not in config:
                print(f"Skipping {key} (Not found in TOML)")
                continue
                
            wanted_songs = config[key]
            song_ids = []
            missing = []
            
            for sname in wanted_songs:
                if sname in song_map:
                    song_ids.append(song_map[sname])
                else:
                    missing.append(sname)
            
            if missing:
                print(f"[{name}] WARNING: Missing songs in DB: {missing}")
            
            # Update
            sub = db.query(Subgroup).filter_by(name=name, franchise_id=franchise.id).first()
            if sub:
                print(f"[{name}] Updating {len(sub.song_ids or [])} -> {len(song_ids)} songs")
                sub.song_ids = song_ids
            else:
                print(f"[{name}] Subgroup not found in DB")
        
        db.commit()
        print("All updates committed.")
        
        # Clear Cache
        db.execute(text("DELETE FROM analysis_results WHERE franchise_id = :fid"), {"fid": franchise.id})
        db.commit()
        print("Cache cleared.")

    finally:
        db.close()

if __name__ == "__main__":
    debug_all_solos()
