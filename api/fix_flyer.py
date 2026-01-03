
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

def fix_flyer():
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check current state
        res = db.execute(text("SELECT name FROM songs WHERE name LIKE 'Flyer%High'")).fetchall()
        print(f"Current songs matching 'Flyer%High': {[r[0] for r in res]}")
        
        # Update
        # We want "Flyer’s High" (curly)
        # We replace "Flyer's High" (straight)
        
        stmt = text("UPDATE songs SET name = 'Flyer’s High' WHERE name = \"Flyer's High\"")
        result = db.execute(stmt)
        print(f"Updated {result.rowcount} rows.")
        db.commit()
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_flyer()
