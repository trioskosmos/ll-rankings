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
                         SubgroupResponse)
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


# NEW ENDPOINTS FOR ADDITIONAL FEATURES

@router.get("/analysis/disputed")
async def get_most_disputed(franchise: str, subgroup: str, db: Session = Depends(get_db)):
    """Get songs with the largest ranking gaps between users"""
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

    data = AnalysisService.compute_most_disputed(
        str(franchise_obj.id), str(subgroup_obj.id), db
    )
    
    return {
        "metadata": {
            "computed_at": datetime.utcnow(),
            "based_on_submissions": len(subgroup_obj.submissions),
        },
        "results": data
    }


@router.get("/analysis/consensus")
async def get_top_bottom_consensus(
    franchise: str, subgroup: str, limit: int = 10, db: Session = Depends(get_db)
):
    """Get songs universally ranked high or low with strong agreement"""
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

    data = AnalysisService.compute_top_bottom_consensus(
        str(franchise_obj.id), str(subgroup_obj.id), db, limit
    )
    
    return {
        "metadata": {
            "computed_at": datetime.utcnow(),
            "based_on_submissions": len(subgroup_obj.submissions),
        },
        "top": data["top"],
        "bottom": data["bottom"]
    }


@router.get("/analysis/outliers")
async def get_outlier_users(franchise: str, subgroup: str, db: Session = Depends(get_db)):
    """Identify users with the most extreme/unique rankings"""
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

    data = AnalysisService.compute_outlier_users(
        str(franchise_obj.id), str(subgroup_obj.id), db
    )
    
    return {
        "metadata": {
            "computed_at": datetime.utcnow(),
            "based_on_submissions": len(subgroup_obj.submissions),
        },
        "results": data
    }


@router.get("/analysis/comebacks")
async def get_comeback_songs(franchise: str, subgroup: str, db: Session = Depends(get_db)):
    """Find sleeper/comeback songs with polarized rankings"""
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

    data = AnalysisService.compute_comeback_songs(
        str(franchise_obj.id), str(subgroup_obj.id), db
    )
    
    return {
        "metadata": {
            "computed_at": datetime.utcnow(),
            "based_on_submissions": len(subgroup_obj.submissions),
        },
        "results": data
    }


@router.get("/analysis/subunits")
async def get_subunit_popularity(franchise: str, db: Session = Depends(get_db)):
    """Analyze performance of different subunits/groups"""
    franchise_obj = db.query(Franchise).filter_by(name=franchise).first()
    if not franchise_obj:
        raise HTTPException(status_code=404, detail="Franchise not found")

    data = AnalysisService.compute_subunit_popularity(
        str(franchise_obj.id), db
    )
    
    sub_count = db.query(Submission).filter_by(franchise_id=franchise_obj.id).count()
    
    return {
        "metadata": {
            "computed_at": datetime.utcnow(),
            "based_on_submissions": sub_count,
        },
        "results": data
    }


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


@router.get("/subgroups", response_model=list[SubgroupResponse])
async def get_franchise_subgroups(franchise: str, db: Session = Depends(get_db)):
    """
    Get all subgroup definitions for a franchise, 
    including resolved song name lists.
    """
    # 1. Validate Franchise
    franchise_obj = db.query(Franchise).filter_by(name=franchise).first()
    if not franchise_obj:
        raise HTTPException(status_code=404, detail="Franchise not found")

    # 2. Fetch all subgroups belonging to this franchise
    subgroups = (
        db.query(Subgroup)
        .filter(Subgroup.franchise_id == franchise_obj.id)
        .all()
    )

    # 3. Transform and Resolve Song Names
    results = []
    for sg in subgroups:
        # Resolve names for IDs stored in the JSON list
        song_names = []
        if sg.song_ids:
            from uuid import UUID
            songs = db.query(Song.name).filter(Song.id.in_([UUID(sid) for sid in sg.song_ids])).all()
            song_names = [s.name for s in songs]

        results.append(SubgroupResponse(
            id=sg.id,
            name=sg.name,
            franchise=franchise_obj.name,
            song_count=len(sg.song_ids) if sg.song_ids else 0,
            is_custom=sg.is_custom,
            is_subunit=sg.is_subunit,
            songs=song_names
        ))

    return results


@router.get("/analysis/head-to-head")
async def get_head_to_head(
    franchise: str,
    subgroup: str,
    user_a: str,
    user_b: str,
    db: Session = Depends(get_db)
):
    """Compare two users' rankings directly"""
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

    result = AnalysisService.compute_head_to_head(
        str(franchise_obj.id), str(subgroup_obj.id), user_a, user_b, db
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
        
    return result


@router.get("/analysis/user-match")
async def get_user_matches(
    franchise: str,
    subgroup: str,
    user: str,
    db: Session = Depends(get_db)
):
    """Find soulmates and nemeses for a user"""
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

    result = AnalysisService.compute_user_match(
        str(franchise_obj.id), str(subgroup_obj.id), user, db
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
        
    return result


@router.get("/analysis/conformity")
async def get_conformity_scores(
    franchise: str,
    subgroup: str,
    db: Session = Depends(get_db)
):
    """Identify Normies and Hipsters based on consensus deviation"""
    franchise_obj = db.query(Franchise).filter_by(name=franchise).first()
    if not franchise_obj:
         raise HTTPException(status_code=404, detail="Franchise not found")
    
    subgroup_obj = db.query(Subgroup).filter(Subgroup.name == subgroup, Subgroup.franchise_id == franchise_obj.id).first()
    if not subgroup_obj:
         raise HTTPException(status_code=404, detail="Subgroup not found")
         
    return AnalysisService.compute_conformity(str(franchise_obj.id), str(subgroup_obj.id), db)


@router.get("/analysis/oshi-bias")
async def get_oshi_bias(
    franchise: str,
    user: str,
    db: Session = Depends(get_db)
):
    """Calculate member bias for a user"""
    franchise_obj = db.query(Franchise).filter_by(name=franchise).first()
    if not franchise_obj:
         raise HTTPException(status_code=404, detail="Franchise not found")
         
    return AnalysisService.compute_oshi_bias(str(franchise_obj.id), user, db)