
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from app.config import settings
import json

def check_db_subgroup():
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get Liella Franchise ID
        fid = db.execute(text("SELECT id FROM franchises WHERE name='liella'")).fetchone()[0]
        
        # Get Subgroup
        row = db.execute(text("SELECT id, song_ids FROM subgroups WHERE name='Kanon Solos' AND franchise_id=:fid"), {"fid": fid}).fetchone()
        
        if not row:
            print("Subgroup 'Kanon Solos' NOT FOUND in DB")
            return

        sid, song_ids = row
        print(f"Subgroup ID: {sid}")
        print(f"Song IDs (Count: {len(song_ids)})")
        
        # Resolve names
        # Assuming song_ids is list of UUID strings
        if not song_ids:
            print("No songs in subgroup.")
        else:
            # SQL IN clause with uuid casting
            # We'll just fetch all songs for franchise and map in python for simplicity
            songs = db.execute(text("SELECT id, name FROM songs WHERE franchise_id=:fid"), {"fid": fid}).fetchall()
            id_map = {str(s[0]): s[1] for s in songs}
            
            found_names = []
            for uid in song_ids:
                if uid in id_map:
                    found_names.append(id_map[uid])
                else:
                    found_names.append(f"UNKNOWN_UUID_{uid}")
            
            found_names.sort()
            for n in found_names:
                print(f" - {n}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_db_subgroup()
