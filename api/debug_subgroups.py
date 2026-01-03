
import os
import sys

# Add api directory to sys.path to import app modules
api_dir = os.path.join(os.getcwd(), 'api')
sys.path.append(api_dir)

from app.database import SessionLocal, init_engine
from app.models import Subgroup, Franchise

init_engine()
db = SessionLocal()
f = db.query(Franchise).filter_by(name="Love Live!").first()
if not f:
    print("Franchise not found")
else:
    sgs = db.query(Subgroup).filter_by(franchise_id=f.id).all()
    print(f"Found {len(sgs)} subgroups:")
    for sg in sgs:
        print(f" - '{sg.name}' (is_subunit={sg.is_subunit}, count={len(sg.song_ids) if sg.song_ids else 0})")
