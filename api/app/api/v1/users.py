# app/api/v1/users.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Franchise, Submission, Song, SubmissionStatus
from typing import List, Dict

router = APIRouter(prefix="/api/v1", tags=["users"])


@router.get("/users/rankings")
async def get_user_rankings(franchise: str, subgroup: str, db: Session = Depends(get_db)):
    """Get all individual user rankings for a franchise/subgroup"""
    
    # Look up franchise
    franchise_obj = db.query(Franchise).filter_by(name=franchise).first()
    if not franchise_obj:
        raise HTTPException(status_code=404, detail="Franchise not found")
    
    # Get all valid submissions for this franchise
    submissions = (
        db.query(Submission)
        .filter(
            Submission.franchise_id == franchise_obj.id,
            Submission.submission_status == SubmissionStatus.VALID,
        )
        .all()
    )
    
    # Get song ID to name mapping
    all_song_ids = set()
    for sub in submissions:
        if sub.parsed_rankings:
            all_song_ids.update(sub.parsed_rankings.keys())
    
    from uuid import UUID
    if all_song_ids:
        songs = db.query(Song).filter(Song.id.in_([UUID(sid) for sid in all_song_ids])).all()
        song_name_map = {str(s.id): s.name for s in songs}
    else:
        song_name_map = {}
    
    # Build response
    result = []
    for sub in submissions:
        if not sub.parsed_rankings:
            continue
            
        # Convert to song names and rankings
        rankings = []
        for song_id, rank in sorted(sub.parsed_rankings.items(), key=lambda x: x[1]):
            song_name = song_name_map.get(song_id, "Unknown")
            rankings.append({
                "song_name": song_name,
                "rank": rank
            })
        
        result.append({
            "username": sub.username,
            "submission_date": sub.created_at,
            "total_songs": len(rankings),
            "rankings": rankings
        })
    
    # Sort by username
    result.sort(key=lambda x: x["username"].lower())
    
    return {
        "franchise": franchise,
        "subgroup": subgroup,
        "total_users": len(result),
        "users": result
    }
