# app/api/v1/submissions.py

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Franchise, Subgroup, Submission, SubmissionStatus
from app.schemas import SubmissionResponse, SubmitRankingRequest, DeleteSubmissionsResponse
from app.services.matching import StrictSongMatcher
from app.services.tie_handling import TieHandlingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["submissions"])

@router.post("/submit", response_model=SubmissionResponse)
async def submit_ranking(request: SubmitRankingRequest, db: Session = Depends(get_db)):
    # 1. Fetch dependencies
    franchise = db.query(Franchise).filter_by(name=request.franchise).first()
    if not franchise:
        raise HTTPException(status_code=404, detail="Franchise not found")

    subgroup = (
        db.query(Subgroup)
        .filter(
            Subgroup.name == request.subgroup_name,
            Subgroup.franchise_id == franchise.id,
        )
        .first()
    )
    if not subgroup:
        raise HTTPException(status_code=404, detail="Subgroup not found")

    # 2. Parse text for songs and conflicts
    matched, conflicts = StrictSongMatcher.parse_ranking_text(
        request.ranking_list, request.franchise, db
    )

    # 3. Create record
    submission = Submission(
        username=request.username,
        franchise_id=franchise.id,
        subgroup_id=subgroup.id,
        raw_ranking_text=request.ranking_list,
    )

    # 4. Handle Failure (Conflicts)
    if conflicts:
        submission.submission_status = SubmissionStatus.CONFLICTED
        submission.conflict_report = conflicts
        db.add(submission)
        db.commit()

        return SubmissionResponse(
            submission_id=submission.id,
            status="CONFLICTED",
            parsed_count=len(matched),
            conflicts=conflicts,
        )

    # 5. Handle Success
    # Transform simple ranks to mean ranks for statistical accuracy
    final_ranks = TieHandlingService.convert_tied_ranks(matched)

    submission.parsed_rankings = final_ranks
    submission.submission_status = SubmissionStatus.VALID
    db.add(submission)
    db.commit()

    return SubmissionResponse(
        submission_id=submission.id,
        status="VALID",
        parsed_count=len(final_ranks),
    )

@router.delete("/submissions/{username}", response_model=DeleteSubmissionsResponse)
async def delete_user_submissions(
    username: str, 
    franchise: str, 
    db: Session = Depends(get_db)
):
    """
    Delete all rankings submitted by a specific username 
    within a franchise.
    """
    # 1. Verify Franchise
    franchise_obj = db.query(Franchise).filter_by(name=franchise).first()
    if not franchise_obj:
        raise HTTPException(status_code=404, detail="Franchise not found")

    # 2. Find and Delete
    query = db.query(Submission).filter(
        Submission.username == username,
        Submission.franchise_id == franchise_obj.id
    )
    
    count = query.count()
    if count == 0:
        return DeleteSubmissionsResponse(
            username=username,
            deleted_count=0,
            message=f"No submissions found for user '{username}'."
        )

    query.delete(synchronize_session=False)
    db.commit()

    logger.info(f"Deleted {count} submissions for user '{username}' in {franchise}")

    return DeleteSubmissionsResponse(
        username=username,
        deleted_count=count,
        message=f"Successfully removed all data for '{username}'. Analysis will refresh on next schedule."
    )