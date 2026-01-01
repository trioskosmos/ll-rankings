# test_import_verbose.py - Verbose test script

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)

# Add the api directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import init_engine, init_db, get_session
from app.seeds.init import DatabaseSeeder

def main():
    try:
        print("=" * 60)
        print("INITIALIZING DATABASE")
        print("=" * 60)
        init_engine()
        init_db()
        
        print("\n" + "=" * 60)
        print("RUNNING SEEDING")
        print("=" * 60)
        db = get_session()
        try:
            DatabaseSeeder.seed_all(db)
            print("\n✅ IMPORT COMPLETE!")
        finally:
            db.close()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
