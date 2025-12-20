# app/schemas.py

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


# Requests
class SubmitRankingRequest(BaseModel):
    username: str
    franchise: str
    subgroup_name: str
    ranking_list: str


# Responses
class ConflictDetail(BaseModel):
    reason: str  # "invalid_format", "song_not_found", "duplicate_song"
    line_num: int
    raw_text: str
    expected_format: Optional[str] = None
    suggestions: Optional[list[str]] = None


class SubmissionResponse(BaseModel):
    submission_id: UUID
    status: str
    parsed_count: int
    # Now uses the structured ConflictDetail
    conflicts: Optional[Dict[str, ConflictDetail]] = None


class SongResponse(BaseModel):
    id: UUID
    name: str
    youtube_url: Optional[str] = None

    class Config:
        from_attributes = True


class SubgroupResponse(BaseModel):
    id: UUID
    name: str
    franchise: str
    song_count: int
    is_custom: bool

    class Config:
        from_attributes = True


class AnalysisMetadata(BaseModel):
    computed_at: datetime
    based_on_submissions: int


class DivergenceMatrixResponse(BaseModel):
    metadata: AnalysisMetadata
    matrix: Dict[str, Dict[str, float]]


class ControversySongResult(BaseModel):
    song_id: UUID
    song_name: str
    avg_rank: float
    controversy_score: float
    cv: float
    bimodality: float


class ControversyResponse(BaseModel):
    metadata: AnalysisMetadata
    results: list[ControversySongResult]


class HotTakeResult(BaseModel):
    username: str
    song_name: str
    user_rank: float
    group_avg: float
    delta: float
    score: float  # Normalized percentage
    take_type: str  # "HOT_TAKE" or "GLAZE"


class HotTakesResponse(BaseModel):
    metadata: AnalysisMetadata
    takes: list[HotTakeResult]


class UserSpiceResult(BaseModel):
    username: str
    global_spice: float
    group_breakdown: Dict[str, float]  # {subgroup_name: spice_score}


class SpiceMeterResponse(BaseModel):
    metadata: AnalysisMetadata
    results: list[UserSpiceResult]


class CommunityRankResult(BaseModel):
    song_id: UUID
    song_name: str
    points: float        # Sum of ranks
    average: float  # Mean of ranks
    submission_count: int


class CommunityRankResponse(BaseModel):
    metadata: AnalysisMetadata
    rankings: list[CommunityRankResult]


class DeleteSubmissionsResponse(BaseModel):
    username: str
    deleted_count: int
    message: str


class TriggerResponse(BaseModel):
    status: str
    message: str
    timestamp: datetime


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime
