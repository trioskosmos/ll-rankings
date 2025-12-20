# app/services/analysis.py

import statistics
from collections import defaultdict
from typing import Dict, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Song, Subgroup, Submission, SubmissionStatus

from app.services.ranking_utils import RelativeRankingService

class AnalysisService:
    @staticmethod
    def compute_divergence_matrix(
        franchise_id: str, subgroup_id: str, db: Session
    ) -> Dict[str, Dict[str, float]]:
        subgroup = db.query(Subgroup).filter_by(id=subgroup_id).first()
        if not subgroup or not subgroup.song_ids:
            return {}

        submissions = (
            db.query(Submission)
            .filter(
                Submission.franchise_id == franchise_id,
                Submission.subgroup_id == subgroup_id,
                Submission.submission_status == SubmissionStatus.VALID,
            )
            .all()
        )

        # Build relativized rankings for every user in this subgroup
        user_rel_rankings = {}
        for sub in submissions:
            # We relativize the master list to the current subgroup's song list
            rel_map = RelativeRankingService.relativize(
                sub.parsed_rankings, 
                subgroup.song_ids
            )
            if rel_map:
                user_rel_rankings[sub.username] = rel_map

        # Pairwise RMS distance calculation using the relative ranks
        users = sorted(list(user_rel_rankings.keys()))
        matrix = {}
        for u1 in users:
            matrix[u1] = {}
            for u2 in users:
                if u1 == u2:
                    matrix[u1][u2] = 0.0
                    continue

                shared_songs = set(user_rel_rankings[u1].keys()) & set(
                    user_rel_rankings[u2].keys()
                )
                if not shared_songs:
                    matrix[u1][u2] = 0.0
                    continue

                sq_diffs = [
                    (user_rel_rankings[u1][sid] - user_rel_rankings[u2][sid]) ** 2
                    for sid in shared_songs
                ]
                rms = (sum(sq_diffs) / len(sq_diffs)) ** 0.5
                matrix[u1][u2] = round(rms, 2)

        return matrix

    @staticmethod
    def compute_controversy(
        franchise_id: str, subgroup_id: str, db: Session
    ) -> list[dict]:
        subgroup = db.query(Subgroup).filter_by(id=subgroup_id).first()
        if not subgroup or not subgroup.song_ids:
            return []

        submissions = (
            db.query(Submission)
            .filter(
                Submission.subgroup_id == subgroup_id,
                Submission.submission_status == SubmissionStatus.VALID,
            )
            .all()
        )

        if not submissions:
            return []

        # 1. Relativize all submissions to the subgroup 1..N scale
        user_rel_rankings = []
        for sub in submissions:
            rel_map = RelativeRankingService.relativize(
                sub.parsed_rankings, 
                subgroup.song_ids
            )
            if rel_map:
                user_rel_rankings.append(rel_map)

        # 2. Pivot data to Song-based lists
        song_rank_collections = defaultdict(list)
        for rel_map in user_rel_rankings:
            for song_id, rank in rel_map.items():
                song_rank_collections[song_id].append(rank)

        # 3. Calculate metrics for each song
        songs = db.query(Song).filter(Song.id.in_(subgroup.song_ids)).all()
        song_name_map = {str(s.id): s.name for s in songs}
        
        results = []
        for song_id, ranks in song_rank_collections.items():
            if len(ranks) < 2:
                continue

            stats = ControversyIndexService.calculate(ranks)

            results.append({
                "song_id": song_id,
                "song_name": song_name_map.get(song_id, "Unknown"),
                "avg_rank": stats["mean"],
                "controversy_score": stats["score"],
                "cv": stats["cv"],
                "bimodality": stats["bimodality_indicator"],
                "range": f"{min(ranks):.0f}-{max(ranks):.0f}"
            })

        # Sort by controversy_score DESC (Most Controversial first)
        return sorted(results, key=lambda x: x["controversy_score"], reverse=True)

    @staticmethod
    def compute_hot_takes(
        franchise_id: str, subgroup_id: str, db: Session
    ) -> list[dict]:
        """
        Calculates the delta between individual user ranks and group averages.
        Returns a list of takes sorted by the magnitude of the deviation.
        """
        subgroup = db.query(Subgroup).filter_by(id=subgroup_id).first()
        if not subgroup or not subgroup.song_ids:
            return []

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

        # 1. Relativize all user rankings
        user_rel_rankings = {}
        for sub in submissions:
            rel_map = RelativeRankingService.relativize(
                sub.parsed_rankings, 
                subgroup.song_ids
            )
            if rel_map:
                user_rel_rankings[sub.username] = rel_map

        # 2. Calculate average relative rank per song
        song_ranks = defaultdict(list)
        for rel_map in user_rel_rankings.values():
            for song_id, rank in rel_map.items():
                song_ranks[song_id].append(rank)

        song_averages = {
            sid: statistics.mean(ranks) for sid, ranks in song_ranks.items()
        }

        # 3. Calculate takes (deviations)
        songs = db.query(Song).filter(Song.id.in_(subgroup.song_ids)).all()
        song_name_map = {str(s.id): s.name for s in songs}
        
        results = []
        song_count = len(subgroup.song_ids)

        for username, rel_map in user_rel_rankings.items():
            for song_id, user_rank in rel_map.items():
                avg_rank = song_averages.get(song_id)
                delta = user_rank - avg_rank
                
                # Normalize the score (same as your .gs logic)
                # Positive score = User ranked it lower (numerically higher) than group = Hot Take
                # Negative score = User ranked it higher (numerically lower) than group = Glaze
                score = (delta / song_count) * 100

                results.append({
                    "username": username,
                    "song_name": song_name_map.get(song_id, "Unknown"),
                    "user_rank": round(user_rank, 1),
                    "group_avg": round(avg_rank, 2),
                    "delta": round(delta, 2),
                    "score": round(score, 2),
                    "take_type": "HOT_TAKE" if score > 0 else "GLAZE"
                })

        # Sort by absolute score (biggest deviations first)
        return sorted(results, key=lambda x: abs(x["score"]), reverse=True)

    @staticmethod
    def compute_spice_meter(franchise_id: str, db: Session) -> list[dict]:
        """
        Calculates the Spice Index for all users across all subgroups.
        Spice = RMS distance from the average rank given by other users.
        """
        subgroups = db.query(Subgroup).filter_by(franchise_id=franchise_id).all()
        user_group_scores = defaultdict(dict)  # {username: {group_name: rms}}
        all_usernames = set()

        for sg in subgroups:
            if not sg.song_ids:
                continue

            submissions = (
                db.query(Submission)
                .filter(
                    Submission.subgroup_id == sg.id,
                    Submission.submission_status == SubmissionStatus.VALID
                ).all()
            )

            if len(submissions) < 2:
                continue

            # 1. Relativize all rankings for this group
            user_rel_map = {}
            for sub in submissions:
                rel = RelativeRankingService.relativize(sub.parsed_rankings, sg.song_ids)
                if rel:
                    user_rel_map[sub.username] = rel
                    all_usernames.add(sub.username)

            # 2. For each user, calculate RMS distance from the "Average of Others"
            for target_user, target_ranks in user_rel_map.items():
                sq_diffs = []

                for song_id, user_rank in target_ranks.items():
                    # Get ranks from all OTHER users for this song
                    other_ranks = [
                        ranks[song_id] 
                        for uname, ranks in user_rel_map.items() 
                        if uname != target_user and song_id in ranks
                    ]

                    if not other_ranks:
                        continue
                    
                    avg_others = statistics.mean(other_ranks)
                    sq_diffs.append((user_rank - avg_others) ** 2)

                if sq_diffs:
                    rms = math.sqrt(statistics.mean(sq_diffs))
                    user_group_scores[target_user][sg.name] = round(rms, 2)

        # 3. Aggregate into final results
        final_results = []
        for username in all_usernames:
            scores = user_group_scores.get(username, {})
            if not scores:
                continue
            
            global_spice = statistics.mean(scores.values()) if scores else 0
            
            final_results.append({
                "username": username,
                "global_spice": round(global_spice, 2),
                "group_breakdown": scores
            })

        # Sort by Global Spice (Spiciest at the top)
        return sorted(final_results, key=lambda x: x["global_spice"], reverse=True)

class ControversyIndexService:
    """
    Refined Controversy Index logic:
    Combines CV (relative variability) with Bimodality (polarization).
    """

    @staticmethod
    def calculate(ranks: list[float]) -> dict:
        if len(ranks) < 2:
            return {
                "std_dev": 0.0,
                "mean": 0.0,
                "cv": 0.0,
                "iqr": 0.0,
                "bimodality_indicator": 1.0,
                "score": 0.0,
            }

        mean = statistics.mean(ranks)
        std_dev = statistics.stdev(ranks)

        # 1. Coefficient of Variation (CV)
        # This makes the index scale-invariant. 
        # Disagreements at the top of the list (low mean) are weighted more heavily.
        cv = std_dev / mean if mean > 0 else 0

        # 2. Bimodality Indicator via IQR
        # Identifies if users are split into camps vs just scattered.
        sorted_ranks = sorted(ranks)
        n = len(sorted_ranks)
        q1 = sorted_ranks[int(n * 0.25)]
        q3 = sorted_ranks[int(n * 0.75)]
        iqr = q3 - q1

        # Logic from your .gs script:
        # If middle 50% spread is > 30% of the mean, it's polarized.
        bimodality_ratio = iqr / mean if mean > 0 else 0
        bimodality_indicator = 1.5 if bimodality_ratio > 0.3 else 1.0

        # 3. Final Composite Score
        controversy_score = cv * bimodality_indicator

        return {
            "std_dev": round(std_dev, 2),
            "mean": round(mean, 2),
            "cv": round(cv, 4),
            "iqr": round(iqr, 2),
            "bimodality_indicator": bimodality_indicator,
            "score": round(controversy_score, 4),
        }