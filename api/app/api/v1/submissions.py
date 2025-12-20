# app/api/v1/submissions.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models import Franchise, Subgroup, Submission, SubmissionStatus
from app.schemas import SubmitRankingRequest, SubmissionResponse
from app.services.matching import StrictSongMatcher
from app.services.tie_handling import TieHandlingService
from app.utils.validators import DataValidator
from app.exceptions import ValidationException, MatchingException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["submissions"])

@router.post("/submit", response_model=SubmissionResponse)
async def submit_ranking(
    request: SubmitRankingRequest,
    db: Session = Depends(get_db)
):
    """Submit anonymous rankings with comprehensive error handling"""
    
    try:
        # Validate inputs
        DataValidator.validate_username(request.username)
        DataValidator.validate_franchise(request.franchise)
        DataValidator.validate_ranking_text(request.ranking_list)
        
        logger.info(f"Processing submission from {request.username} for {request.franchise}")
        
        # Validate franchise exists
        franchise = db.query(Franchise).filter_by(name=request.franchise).first()
        if not franchise:
            raise ValidationException(f"Franchise '{request.franchise}' not found")
        
        # Validate subgroup exists
        subgroup = db.query(Subgroup).filter(
            Subgroup.name == request.subgroup_name,
            Subgroup.franchise_id == franchise.id
        ).first()
        if not subgroup:
            raise ValidationException(
                f"Subgroup '{request.subgroup_name}' not found for franchise '{request.franchise}'"
            )
        
        # Match songs
        matched, conflicts = StrictSongMatcher.parse_ranking_text(
            request.ranking_list,
            request.franchise,
            db
        )
        
        # Create submission record
        submission = Submission(
            username=request.username,
            franchise_id=franchise.id,
            subgroup_id=subgroup.id,
            raw_ranking_text=request.ranking_list
        )
        
        if conflicts:
            submission.submission_status = SubmissionStatus.CONFLICTED
            submission.conflict_report = conflicts
            db.add(submission)
            db.commit()
            
            logger.warning(f"Submission {submission.id} has {len(conflicts)} conflicts")
            
            return SubmissionResponse(
                submission_id=submission.id,
                status="CONFLICTED",
                parsed_count=len(matched),
                conflicts=submission.conflict_report
            )
        
        # Handle ties
        final_ranks = TieHandlingService.convert_tied_ranks(matched)
        
        submission.parsed_rankings = final_ranks
        submission.submission_status = SubmissionStatus.VALID
        db.add(submission)
        db.commit()
        
        logger.info(f"Submission {submission.id} accepted with {len(final_ranks)} songs")
        
        return SubmissionResponse(
            submission_id=submission.id,
            status="VALID",
            parsed_count=len(final_ranks),
            conflicts=None
        )
    
    except ValidationException as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    
    except MatchingException as e:
        logger.warning(f"Matching error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error in submission: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")