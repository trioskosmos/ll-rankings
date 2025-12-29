import sys
sys.path.insert(0, 'api')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Submission, Subgroup, Franchise, SubmissionStatus
from app.services.analysis import AnalysisService, to_uuid
from uuid import UUID

engine = create_engine('sqlite:///api/rankings.db')
Session = sessionmaker(bind=engine)
db = Session()

try:
    # Get franchise
    f = db.query(Franchise).filter_by(name='liella').first()
    print('Franchise ID:', f.id)
    
    # Get subgroup
    sg = db.query(Subgroup).filter(Subgroup.name == 'All Songs', Subgroup.franchise_id == f.id).first()
    print('Subgroup ID:', sg.id)
    
    # Test the service
    result = AnalysisService.compute_head_to_head(
        str(f.id), str(sg.id), 'Rumi', 'kusa', db
    )
    print('Result:', result)
    
except Exception as e:
    import traceback
    print('ERROR:')
    traceback.print_exc()
finally:
    db.close()
