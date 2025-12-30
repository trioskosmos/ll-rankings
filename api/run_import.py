from app.database import init_engine, get_session
from app.seeds.import_rankings import import_user_rankings
import logging

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

# Initialize database engine
init_engine()
db = get_session()

try:
    print("Starting rankings import manually...")
    import_user_rankings(db)
    print("Import complete.")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
