
from sqlalchemy import create_engine, text
from app.config import settings
import json

def verify_chisato():
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT song_ids FROM subgroups WHERE name='Chisato Solos'")).fetchone()
        if res:
            ids = json.loads(res[0])
            print(f"Chisato Solos Count: {len(ids)}")
        else:
            print("Chisato Solos not found")

if __name__ == "__main__":
    verify_chisato()
