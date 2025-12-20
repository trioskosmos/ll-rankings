# app/services/analysis.py

import statistics
from collections import defaultdict
from typing import Dict, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Song, Subgroup, Submission, SubmissionStatus


class AnalysisService:
    @staticmethod
    def compute_divergence_matrix(
        franchise_id: str, subgroup_id: str, db: Session
    ) -> Dict[str, Dict[str, float]]:
        """
        Compute pairwise divergence matrix for a subgroup.
        Only uses songs in the subgroup.
        """
        subgroup = db.query(Subgroup).filter_by(id=subgroup_id).first()
        if not subgroup:
            return {}

        # Get all valid submissions for this subgroup
        submissions = (
            db.query(Submission)
            .filter(
                Submission.franchise_id == franchise_id,
                Submission.subgroup_id == subgroup_id,
                Submission.submission_status == SubmissionStatus.VALID,
            )
            .all()
        )

        if not submissions:
            return {}

        # Build user rankings map (filtered to subgroup songs)
        user_rankings = defaultdict(dict)
        subgroup_song_ids = set(subgroup.song_ids)

        for sub in submissions:
            for song_id, rank in sub.parsed_rankings.items():
                if song_id in subgroup_song_ids:
                    user_rankings[sub.username][song_id] = rank

        # Compute pairwise divergence
        users = sorted(list(user_rankings.keys()))
        matrix = {}

        for user1 in users:
            matrix[user1] = {}
            for user2 in users:
                if user1 == user2:
                    matrix[user1][user2] = 0.0
                    continue

                # RMS distance on shared songs
                shared_songs = set(user_rankings[user1].keys()) & set(
                    user_rankings[user2].keys()
                )

                if not shared_songs:
                    matrix[user1][user2] = 0.0
                    continue

                sq_diffs = [
                    (user_rankings[user1][sid] - user_rankings[user2][sid]) ** 2
                    for sid in shared_songs
                ]
                rms = (sum(sq_diffs) / len(sq_diffs)) ** 0.5
                matrix[user1][user2] = round(rms, 2)

        return matrix

    @staticmethod
    def compute_controversy(
        franchise_id: str, subgroup_id: str, db: Session
    ) -> List[Dict]:
        """
        Compute controversy index for each song in subgroup.
        """
        subgroup = db.query(Subgroup).filter_by(id=subgroup_id).first()
        if not subgroup:
            return []

        # Get submissions
        submissions = (
            db.query(Submission)
            .filter(
                Submission.franchise_id == franchise_id,
                Submission.subgroup_id == subgroup_id,
                Submission.submission_status == SubmissionStatus.VALID,
            )
            .all()
        )

        if not submissions:
            return []

        # Get songs in this subgroup
        songs = db.query(Song).filter(Song.id.in_(subgroup.song_ids)).all()
        song_by_id = {str(s.id): s for s in songs}

        results = []

        for song in songs:
            song_id_str = str(song.id)
            ranks = [
                sub.parsed_rankings[song_id_str]
                for sub in submissions
                if song_id_str in sub.parsed_rankings
            ]

            if len(ranks) < 2:
                continue

            controversy = ControversyIndexService.calculate(ranks)

            results.append(
                {
                    "song_id": str(song.id),
                    "song_name": song.name,
                    "avg_rank": round(statistics.mean(ranks), 2),
                    "controversy_score": round(controversy["score"], 4),
                    "cv": round(controversy["cv"], 4),
                    "bimodality": controversy["bimodality_indicator"],
                }
            )

        return sorted(results, key=lambda x: x["controversy_score"], reverse=True)


class ControversyIndexService:
    """Calculate controversy metrics for a set of ranks"""

    @staticmethod
    def calculate(ranks: List[float]) -> Dict:
        """
        Calculate controversy index.
        Returns: {score, cv, bimodality_indicator, stdDev, mean, iqr}
        """
        if len(ranks) < 2:
            return {
                "stdDev": 0,
                "mean": 0,
                "cv": 0,
                "iqr": 0,
                "bimodality_indicator": 1.0,
                "score": 0,
            }

        mean = statistics.mean(ranks)
        variance = statistics.variance(ranks)
        stdDev = variance**0.5

        # Coefficient of Variation
        cv = stdDev / mean if mean > 0 else 0

        # Quartile analysis
        sorted_ranks = sorted(ranks)
        q1_idx = len(sorted_ranks) // 4
        q3_idx = (3 * len(sorted_ranks)) // 4
        q1 = sorted_ranks[q1_idx]
        q3 = sorted_ranks[q3_idx]
        iqr = q3 - q1

        # Bimodality indicator
        bimodality_ratio = iqr / mean if mean > 0 else 0
        bimodality_indicator = 1.5 if bimodality_ratio > 0.3 else 1.0

        # Final score
        controversy_score = cv * bimodality_indicator

        return {
            "stdDev": round(stdDev, 2),
            "mean": round(mean, 2),
            "cv": round(cv, 4),
            "iqr": round(iqr, 2),
            "bimodality_indicator": bimodality_indicator,
            "score": round(controversy_score, 4),
        }
