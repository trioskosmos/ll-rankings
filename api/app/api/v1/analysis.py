# app/api/v1/analysis.py

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.jobs.analysis_scheduler import recompute_all_analyses, scheduler
from app.models import AnalysisResult, Franchise, Subgroup, Submission, Song
from app.schemas import (AnalysisMetadata, CommunityRankResponse,
                         ControversyResponse, DivergenceMatrixResponse,
                         HotTakesResponse, SpiceMeterResponse, TriggerResponse,
                         SubunitResponse)
from app.services.analysis import AnalysisService

router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.get("/analysis/rankings", response_model=CommunityRankResponse)
async def get_community_rankings(
    franchise: str, subgroup: str, db: Session = Depends(get_db)
):
    """Get the community-wide leaderboard for a subgroup"""
    franchise_obj = db.query(Franchise).filter_by(name=franchise).first()
    if not franchise_obj:
        raise HTTPException(status_code=404, detail="Franchise not found")

    subgroup_obj = (
        db.query(Subgroup)
        .filter(
            Subgroup.name == subgroup, Subgroup.franchise_id == franchise_obj.id
        )
        .first()
    )
    if not subgroup_obj:
        raise HTTPException(status_code=404, detail="Subgroup not found")

    result = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.franchise_id == franchise_obj.id,
            AnalysisResult.subgroup_id == subgroup_obj.id,
            AnalysisResult.analysis_type == "COMMUNITY_RANK",
        )
        .first()
    )

    if not result:
        data = AnalysisService.compute_community_rankings(
            str(franchise_obj.id), str(subgroup_obj.id), db
        )
        return CommunityRankResponse(
            metadata=AnalysisMetadata(
                computed_at=datetime.utcnow(),
                based_on_submissions=len(subgroup_obj.submissions),
            ),
            rankings=data,
        )

    return CommunityRankResponse(
        metadata=AnalysisMetadata(
            computed_at=result.computed_at,
            based_on_submissions=result.based_on_submissions,
        ),
        rankings=result.result_data,
    )


@router.get("/analysis/divergence", response_model=DivergenceMatrixResponse)
async def get_divergence_matrix(
    franchise: str, subgroup: str, db: Session = Depends(get_db)
):
    """Get divergence matrix for a subgroup"""
    franchise_obj = db.query(Franchise).filter_by(name=franchise).first()
    if not franchise_obj:
        raise HTTPException(status_code=404, detail="Franchise not found")

    subgroup_obj = (
        db.query(Subgroup)
        .filter(Subgroup.name == subgroup, Subgroup.franchise_id == franchise_obj.id)
        .first()
    )
    if not subgroup_obj:
        raise HTTPException(status_code=404, detail="Subgroup not found")

    result = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.franchise_id == franchise_obj.id,
            AnalysisResult.subgroup_id == subgroup_obj.id,
            AnalysisResult.analysis_type == "DIVERGENCE",
        )
        .first()
    )

    if not result:
        # Divergence matrices are computationally heavy; fallback to live
        data = AnalysisService.compute_divergence_matrix(
            str(franchise_obj.id), str(subgroup_obj.id), db
        )
        return DivergenceMatrixResponse(
            metadata=AnalysisMetadata(
                computed_at=datetime.utcnow(),
                based_on_submissions=len(subgroup_obj.submissions),
            ),
            matrix=data,
        )

    return DivergenceMatrixResponse(
        metadata=AnalysisMetadata(
            computed_at=result.computed_at,
            based_on_submissions=result.based_on_submissions,
        ),
        matrix=result.result_data,
    )


@router.get("/analysis/controversy", response_model=ControversyResponse)
async def get_controversy(franchise: str, subgroup: str, db: Session = Depends(get_db)):
    """Get controversy analysis for a subgroup"""
    franchise_obj = db.query(Franchise).filter_by(name=franchise).first()
    if not franchise_obj:
        raise HTTPException(status_code=404, detail="Franchise not found")

    subgroup_obj = (
        db.query(Subgroup)
        .filter(Subgroup.name == subgroup, Subgroup.franchise_id == franchise_obj.id)
        .first()
    )
    if not subgroup_obj:
        raise HTTPException(status_code=404, detail="Subgroup not found")

    result = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.franchise_id == franchise_obj.id,
            AnalysisResult.subgroup_id == subgroup_obj.id,
            AnalysisResult.analysis_type == "CONTROVERSY",
        )
        .first()
    )

    if not result:
        data = AnalysisService.compute_controversy(
            str(franchise_obj.id), str(subgroup_obj.id), db
        )
        return ControversyResponse(
            metadata=AnalysisMetadata(
                computed_at=datetime.utcnow(),
                based_on_submissions=len(subgroup_obj.submissions),
            ),
            results=data,
        )

    return ControversyResponse(
        metadata=AnalysisMetadata(
            computed_at=result.computed_at,
            based_on_submissions=result.based_on_submissions,
        ),
        results=result.result_data,
    )


@router.get("/analysis/takes", response_model=HotTakesResponse)
async def get_hot_takes(franchise: str, subgroup: str, db: Session = Depends(get_db)):
    """Identify the biggest glazes and hot takes in a subgroup"""
    franchise_obj = db.query(Franchise).filter_by(name=franchise).first()
    if not franchise_obj:
        raise HTTPException(status_code=404, detail="Franchise not found")

    subgroup_obj = (
        db.query(Subgroup)
        .filter(Subgroup.name == subgroup, Subgroup.franchise_id == franchise_obj.id)
        .first()
    )
    if not subgroup_obj:
        raise HTTPException(status_code=404, detail="Subgroup not found")

    result = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.franchise_id == franchise_obj.id,
            AnalysisResult.subgroup_id == subgroup_obj.id,
            AnalysisResult.analysis_type == "TAKES",
        )
        .first()
    )

    if not result:
        data = AnalysisService.compute_hot_takes(
            str(franchise_obj.id), str(subgroup_obj.id), db
        )
        return HotTakesResponse(
            metadata=AnalysisMetadata(
                computed_at=datetime.utcnow(),
                based_on_submissions=len(subgroup_obj.submissions),
            ),
            takes=data,
        )

    return HotTakesResponse(
        metadata=AnalysisMetadata(
            computed_at=result.computed_at,
            based_on_submissions=result.based_on_submissions,
        ),
        takes=result.result_data,
    )


@router.get("/analysis/spice", response_model=SpiceMeterResponse)
async def get_spice_meter(franchise: str, db: Session = Depends(get_db)):
    """Get the Spice Meter ranking for all users in a franchise"""
    franchise_obj = db.query(Franchise).filter_by(name=franchise).first()
    if not franchise_obj:
        raise HTTPException(status_code=404, detail="Franchise not found")

    result = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.franchise_id == franchise_obj.id,
            AnalysisResult.subgroup_id is None,
            AnalysisResult.analysis_type == "SPICE",
        )
        .first()
    )

    if not result:
        data = AnalysisService.compute_spice_meter(str(franchise_obj.id), db)
        sub_count = (
            db.query(Submission).filter_by(franchise_id=franchise_obj.id).count()
        )

        return SpiceMeterResponse(
            metadata=AnalysisMetadata(
                computed_at=datetime.utcnow(), based_on_submissions=sub_count
            ),
            results=data,
        )

    return SpiceMeterResponse(
        metadata=AnalysisMetadata(
            computed_at=result.computed_at,
            based_on_submissions=result.based_on_submissions,
        ),
        results=result.result_data,
    )


@router.post("/analysis/trigger", response_model=TriggerResponse)
async def trigger_manual_analysis(background_tasks: BackgroundTasks):
    """
    Manually trigger a full recomputation of all statistical metrics.
    Prevents multiple simultaneous runs.
    """
    current_jobs = scheduler.get_jobs()
    for job in current_jobs:
        if job.id == "recompute_all" and job.next_run_time is None:
            raise HTTPException(
                status_code=409,
                detail="Analysis recomputation is already in progress. Please wait.",
            )

    background_tasks.add_task(recompute_all_analyses)

    return TriggerResponse(
        status="accepted",
        message="Analysis recomputation started in the background.",
        timestamp=datetime.utcnow(),
    )

@router.get("/analysis/subunits", response_model=SubunitResponse)
async def get_subunits(franchise: str, db: Session = Depends(get_db)):
    """Get subunits for franchise"""
    franchise_obj = db.query(Franchise).filter_by(name=franchise).first()
    if not franchise_obj:
        raise HTTPException(status_code=404, detail="Franchise not found")

    subunits = (
        db.query(Subgroup)
        .filter(
            Subgroup.franchise_id == franchise_obj.id,
            Subgroup.is_subunit
        )
    )

    grouped_songs = dict()

    for subunit in subunits:
        songs = db.query(Song).filter(Song.id.in_(subunit.song_ids)).all()
        grouped_songs[subunit.name] = [song.name for song in songs]

    return SubunitResponse(results = grouped_songs)