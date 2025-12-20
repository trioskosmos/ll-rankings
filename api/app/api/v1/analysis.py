# app/api/v1/analysis.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AnalysisResult, Franchise, Subgroup
from app.schemas import (AnalysisMetadata, ControversyResponse,
                         DivergenceMatrixResponse)
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

    if not result:
        raise HTTPException(status_code=404, detail="Analysis not yet computed")

    return ControversyResponse(
        metadata=AnalysisMetadata(
            computed_at=result.computed_at,
            based_on_submissions=result.based_on_submissions,
        ),
        results=result.result_data,
    )
