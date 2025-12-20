# app/api/v1/health.py

from fastapi import APIRouter, Depends
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from app import database  # Module import
from app.models import Franchise, Song, Subgroup, Submission
from app.schemas import HealthResponse

router = APIRouter(prefix="/api/v1", tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    db_status = await database.check_db_health()
    return HealthResponse(
        status="ok",
        database=db_status,
        timestamp=datetime.utcnow()
    )

@router.get("/health/database")
async def database_diagnostics(db: Session = Depends(database.get_db)):
    """Detailed database diagnostics"""
    
    franchise_count = db.query(func.count(Franchise.id)).scalar()
    song_count = db.query(func.count(Song.id)).scalar()
    subgroup_count = db.query(func.count(Subgroup.id)).scalar()
    submission_count = db.query(func.count(Submission.id)).scalar()
    
    # Get Liella-specific counts
    liella = db.query(Franchise).filter_by(name="liella").first()
    liella_songs = 0
    liella_subgroups = 0
    
    if liella:
        liella_songs = db.query(func.count(Song.id)).filter(
            Song.franchise_id == liella.id
        ).scalar()
        liella_subgroups = db.query(func.count(Subgroup.id)).filter(
            Subgroup.franchise_id == liella.id
        ).scalar()
    
    # Get all subgroup details
    subgroups = db.query(Subgroup).all()
    subgroup_details = [
        {
            "name": sg.name,
            "song_count": len(sg.song_ids) if sg.song_ids else 0,
            "is_custom": sg.is_custom
        }
        for sg in subgroups
    ]
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow(),
        "totals": {
            "franchises": franchise_count,
            "songs": song_count,
            "subgroups": subgroup_count,
            "submissions": submission_count
        },
        "liella": {
            "songs": liella_songs,
            "subgroups": liella_subgroups,
            "franchise_exists": liella is not None
        },
        "subgroups_detail": subgroup_details,
        "verification": {
            "expected_songs": 147,
            "expected_subgroups": 8,
            "songs_match": liella_songs == 147,
            "subgroups_match": liella_subgroups == 8,
            "all_pass": liella_songs == 147 and liella_subgroups == 8
        }
    }

@router.get("/health/songs")
async def list_all_songs(db: Session = Depends(database.get_db)):
    """List all Liella songs for verification"""
    
    songs = db.query(Song).filter(
        Song.franchise_id == (
            db.query(Franchise.id).filter_by(name="liella").subquery()
        )
    ).order_by(Song.name).all()
    
    return {
        "total_count": len(songs),
        "songs": [
            {"id": str(s.id), "name": s.name, "youtube_url": s.youtube_url}
            for s in songs
        ]
    }