# app/api/v1/analysis.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AnalysisResult, Franchise, Subgroup
from app.schemas import (    AnalysisMetadata,
    ControversyResponse,
    DivergenceMatrixResponse,
    HotTakesResponse,      
    SpiceMeterResponse)
from app.services.analysis import AnalysisService

router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.get("/analysis/divergence")
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
        raise HTTPException(status_code=404, detail="Analysis not yet computed")

    return DivergenceMatrixResponse(
        metadata=AnalysisMetadata(
            computed_at=result.computed_at,
            based_on_submissions=result.based_on_submissions,
        ),
        matrix=result.result_data,
    )


@router.get("/analysis/controversy")
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

    # For hot takes, we compute them on-demand or fetch from the cache
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
        # Fallback if scheduler hasn't run
        data = AnalysisService.compute_hot_takes(
            str(franchise_obj.id), str(subgroup_obj.id), db
        )
        return HotTakesResponse(
            metadata=AnalysisMetadata(
                computed_at=datetime.utcnow(),
                based_on_submissions=len(subgroup_obj.submissions)
            ),
            takes=data
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

    # Check if we have a cached Global Spice analysis
    # (Note: You may need to add "SPICE" to your AnalysisResult types)
    result = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.franchise_id == franchise_obj.id,
            AnalysisResult.analysis_type == "SPICE",
        )
        .first()
    )

    if not result:
        data = AnalysisService.compute_spice_meter(str(franchise_obj.id), db)
        return SpiceMeterResponse(
            metadata=AnalysisMetadata(
                computed_at=datetime.utcnow(),
                based_on_submissions=db.query(Submission).filter_by(franchise_id=franchise_obj.id).count()
            ),
            results=data
        )

    return SpiceMeterResponse(
        metadata=AnalysisMetadata(
            computed_at=result.computed_at,
            based_on_submissions=result.based_on_submissions,
        ),
        results=result.result_data,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Analysis not yet computed")

    return ControversyResponse(
        metadata=AnalysisMetadata(
            computed_at=result.computed_at,
            based_on_submissions=result.based_on_submissions,
        ),
        results=result.result_data,
    )
