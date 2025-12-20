# app/models.py

import enum
import uuid
from datetime import datetime

from sqlalchemy import (JSON, UUID, Boolean, Column, DateTime, Enum,
                        ForeignKey, Integer, String, UniqueConstraint, func)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Franchise(Base):
    __tablename__ = "franchises"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True)  # "liella", "u's", etc
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    songs = relationship(
        "Song", back_populates="franchise", cascade="all, delete-orphan"
    )
    subgroups = relationship(
        "Subgroup", back_populates="franchise", cascade="all, delete-orphan"
    )
    submissions = relationship(
        "Submission", back_populates="franchise", cascade="all, delete-orphan"
    )
    analyses = relationship(
        "AnalysisResult", back_populates="franchise", cascade="all, delete-orphan"
    )


class Song(Base):
    __tablename__ = "songs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    youtube_url = Column(String, nullable=True)
    franchise_id = Column(UUID(as_uuid=True), ForeignKey("franchises.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    franchise = relationship("Franchise", back_populates="songs")

    __table_args__ = (
        UniqueConstraint("name", "franchise_id", name="uq_song_per_franchise"),
    )


class Subgroup(Base):
    __tablename__ = "subgroups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)  # "All Songs", "Solos", "CatChu!", etc
    franchise_id = Column(UUID(as_uuid=True), ForeignKey("franchises.id"))
    song_ids = Column(JSON)  # List of UUID strings
    is_custom = Column(Boolean, default=False)
    is_subunit = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    franchise = relationship("Franchise", back_populates="subgroups")
    submissions = relationship("Submission", back_populates="subgroup")
    analyses = relationship("AnalysisResult", back_populates="subgroup")

    __table_args__ = (
        UniqueConstraint("name", "franchise_id", name="uq_subgroup_per_franchise"),
    )


class SubmissionStatus(str, enum.Enum):
    PENDING = "pending"
    VALID = "valid"
    CONFLICTED = "conflicted"
    FAILED = "failed"


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String)  # Anonymous
    franchise_id = Column(UUID(as_uuid=True), ForeignKey("franchises.id"))
    subgroup_id = Column(UUID(as_uuid=True), ForeignKey("subgroups.id"))

    raw_ranking_text = Column(String)
    parsed_rankings = Column(
        JSON
    )  # {song_id: rank} as strings since JSON doesn't preserve UUID

    submission_status = Column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING)
    conflict_report = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    franchise = relationship("Franchise", back_populates="submissions")
    subgroup = relationship("Subgroup", back_populates="submissions")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    franchise_id = Column(UUID(as_uuid=True), ForeignKey("franchises.id"))
    subgroup_id = Column(UUID(as_uuid=True), ForeignKey("subgroups.id"))

    analysis_type = Column(String)  # "DIVERGENCE", "TAKES", "CONTROVERSY", "SPICE"
    result_data = Column(JSON)

    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    based_on_submissions = Column(Integer, default=0)

    franchise = relationship("Franchise", back_populates="analyses")
    subgroup = relationship("Subgroup", back_populates="analyses")

    __table_args__ = (
        UniqueConstraint(
            "franchise_id", "subgroup_id", "analysis_type", name="uq_analysis_per_group"
        ),
    )
