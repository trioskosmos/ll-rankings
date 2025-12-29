# app/services/analysis.py

import statistics
from collections import defaultdict
from typing import Dict, List, Union
from uuid import UUID
import math

from sqlalchemy.orm import Session
from app.models import Song, Subgroup, Submission, SubmissionStatus
from app.services.ranking_utils import RelativeRankingService


def to_uuid(val: Union[str, UUID]) -> UUID:
    """Convert string or UUID to UUID object"""
    if isinstance(val, UUID):
        return val
    return UUID(val)

class AnalysisService:
    @staticmethod
    def compute_divergence_matrix(
        franchise_id: str, subgroup_id: str, db: Session
    ) -> Dict[str, Dict[str, float]]:
        subgroup = db.query(Subgroup).filter_by(id=to_uuid(subgroup_id)).first()
        if not subgroup or not subgroup.song_ids:
            return {}

        # Fetch ALL valid submissions for this franchise
        submissions = (
            db.query(Submission)
            .filter(
                Submission.franchise_id == to_uuid(franchise_id),
                Submission.submission_status == SubmissionStatus.VALID,
            )
            .all()
        )

        user_rel_rankings = {}
        for sub in submissions:
            rel_map = RelativeRankingService.relativize(
                sub.parsed_rankings, 
                subgroup.song_ids
            )
            if rel_map:
                user_rel_rankings[sub.username] = rel_map

        users = sorted(list(user_rel_rankings.keys()))
        matrix = {}
        for user1 in users:
            matrix[user1] = {}
            for user2 in users:
                if user1 == user2:
                    matrix[user1][user2] = 0.0
                    continue

                shared_songs = set(user_rel_rankings[user1].keys()) & set(
                    user_rel_rankings[user2].keys()
                )
                if not shared_songs:
                    matrix[user1][user2] = 0.0
                    continue

                sq_diffs = [
                    (user_rel_rankings[user1][sid] - user_rel_rankings[user2][sid]) ** 2
                    for sid in shared_songs
                ]
                rms = (sum(sq_diffs) / len(sq_diffs)) ** 0.5
                matrix[user1][user2] = round(rms, 2)

        return matrix

    @staticmethod
    def compute_controversy(
        franchise_id: str, subgroup_id: str, db: Session
    ) -> list[dict]:
        subgroup = db.query(Subgroup).filter_by(id=to_uuid(subgroup_id)).first()
        if not subgroup or not subgroup.song_ids:
            return []

        submissions = (
            db.query(Submission)
            .filter(
                Submission.franchise_id == to_uuid(franchise_id),
                Submission.submission_status == SubmissionStatus.VALID,
            )
            .all()
        )

        user_rel_rankings = []
        for sub in submissions:
            rel_map = RelativeRankingService.relativize(
                sub.parsed_rankings, 
                subgroup.song_ids
            )
            if rel_map:
                user_rel_rankings.append(rel_map)

        if not user_rel_rankings:
            return []

        song_rank_collections = defaultdict(list)
        for rel_map in user_rel_rankings:
            for song_id, rank in rel_map.items():
                song_rank_collections[song_id].append(rank)

        songs = db.query(Song).filter(Song.id.in_([UUID(sid) for sid in subgroup.song_ids])).all()
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

        return sorted(results, key=lambda x: x["controversy_score"], reverse=True)

    @staticmethod
    def compute_hot_takes(
        franchise_id: str, subgroup_id: str, db: Session
    ) -> list[dict]:
        subgroup = db.query(Subgroup).filter_by(id=to_uuid(subgroup_id)).first()
        if not subgroup or not subgroup.song_ids:
            return []

        submissions = (
            db.query(Submission)
            .filter(
                Submission.franchise_id == to_uuid(franchise_id),
                Submission.submission_status == SubmissionStatus.VALID,
            )
            .all()
        )

        user_rel_rankings = {}
        for sub in submissions:
            rel_map = RelativeRankingService.relativize(
                sub.parsed_rankings, 
                subgroup.song_ids
            )
            if rel_map:
                user_rel_rankings[sub.username] = rel_map

        if not user_rel_rankings:
            return []

        song_ranks = defaultdict(list)
        for rel_map in user_rel_rankings.values():
            for song_id, rank in rel_map.items():
                song_ranks[song_id].append(rank)

        song_averages = {
            sid: statistics.mean(ranks) for sid, ranks in song_ranks.items()
        }

        songs = db.query(Song).filter(Song.id.in_([UUID(sid) for sid in subgroup.song_ids])).all()
        song_name_map = {str(s.id): s.name for s in songs}
        
        results = []
        song_count = len(subgroup.song_ids)

        for username, rel_map in user_rel_rankings.items():
            for song_id, user_rank in rel_map.items():
                avg_rank = song_averages.get(song_id)
                delta = user_rank - avg_rank
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

        return sorted(results, key=lambda x: abs(x["score"]), reverse=True)

    @staticmethod
    def compute_spice_meter(franchise_id: str, db: Session) -> list[dict]:
        subgroups = db.query(Subgroup).filter_by(franchise_id=to_uuid(franchise_id)).all()
        user_raw_data = defaultdict(dict)
        all_usernames = set()

        for sg in subgroups:
            if not sg.song_ids or not isinstance(sg.song_ids, list):
                continue
            
            song_count = len(sg.song_ids)
            # Fetch all franchise data to determine if this user has songs for this group
            submissions = (
                db.query(Submission)
                .filter(
                    Submission.franchise_id == to_uuid(franchise_id),
                    Submission.submission_status == SubmissionStatus.VALID
                ).all()
            )

            user_rel_map = {}
            for sub in submissions:
                rel = RelativeRankingService.relativize(sub.parsed_rankings, sg.song_ids)
                if rel:
                    user_rel_map[sub.username] = rel
                    all_usernames.add(sub.username)

            if len(user_rel_map) < 2:
                continue

            for target_user, target_ranks in user_rel_map.items():
                sq_diffs = []
                for song_id, user_rank in target_ranks.items():
                    other_ranks = [
                        ranks[song_id] 
                        for uname, ranks in user_rel_map.items() 
                        if uname != target_user and song_id in ranks
                    ]
                    if other_ranks:
                        avg_others = statistics.mean(other_ranks)
                        sq_diffs.append((user_rank - avg_others) ** 2)

                if sq_diffs:
                    rms = math.sqrt(statistics.mean(sq_diffs))
                    user_raw_data[target_user][sg.name] = {
                        "spice": round(rms, 2),
                        "weight": song_count
                    }

        final_results = []
        for username in all_usernames:
            group_results = user_raw_data.get(username, {})
            if not group_results:
                continue
            
            weighted_spice_sum = 0.0
            total_weight = 0
            breakdown = {}

            for group_name, data in group_results.items():
                weighted_spice_sum += (data["spice"] * data["weight"])
                total_weight += data["weight"]
                breakdown[group_name] = data["spice"]
            
            global_spice = weighted_spice_sum / total_weight if total_weight > 0 else 0
            final_results.append({
                "username": username,
                "global_spice": round(global_spice, 2),
                "group_breakdown": breakdown
            })

        return sorted(final_results, key=lambda x: x["global_spice"], reverse=True)

    @staticmethod
    def compute_community_rankings(
        franchise_id: str, subgroup_id: str, db: Session
    ) -> list[dict]:
        subgroup = db.query(Subgroup).filter_by(id=to_uuid(subgroup_id)).first()
        if not subgroup or not subgroup.song_ids:
            return []

        submissions = (
            db.query(Submission)
            .filter(
                Submission.franchise_id == to_uuid(franchise_id),
                Submission.submission_status == SubmissionStatus.VALID,
            )
            .all()
        )

        user_rel_rankings = []
        for sub in submissions:
            rel_map = RelativeRankingService.relativize(
                sub.parsed_rankings, 
                subgroup.song_ids
            )
            if rel_map:
                user_rel_rankings.append(rel_map)

        if not user_rel_rankings:
            return []

        song_stats = defaultdict(list)
        for rel_map in user_rel_rankings:
            for song_id, rank in rel_map.items():
                song_stats[song_id].append(rank)

        songs = db.query(Song).filter(Song.id.in_([UUID(sid) for sid in subgroup.song_ids])).all()
        song_name_map = {str(s.id): s.name for s in songs}
        
        results = []
        for song_id, ranks in song_stats.items():
            avg = statistics.mean(ranks)
            results.append({
                "song_id": song_id,
                "song_name": song_name_map.get(song_id, "Unknown"),
                "points": round(sum(ranks), 2),
                "average": round(avg, 2),
                "submission_count": len(ranks)
            })

        return sorted(results, key=lambda x: x["average"])

    @staticmethod
    def compute_most_disputed(
        franchise_id: str, subgroup_id: str, db: Session
    ) -> list[dict]:
        """Find songs with the largest rank gap between users"""
        subgroup = db.query(Subgroup).filter_by(id=to_uuid(subgroup_id)).first()
        if not subgroup or not subgroup.song_ids:
            return []

        submissions = (
            db.query(Submission)
            .filter(
                Submission.franchise_id == to_uuid(franchise_id),
                Submission.submission_status == SubmissionStatus.VALID,
            )
            .all()
        )

        user_rel_rankings = []
        for sub in submissions:
            rel_map = RelativeRankingService.relativize(
                sub.parsed_rankings, 
                subgroup.song_ids
            )
            if rel_map:
                user_rel_rankings.append(rel_map)

        if not user_rel_rankings:
            return []

        song_ranks = defaultdict(list)
        for rel_map in user_rel_rankings:
            for song_id, rank in rel_map.items():
                song_ranks[song_id].append(rank)


        songs = db.query(Song).filter(Song.id.in_([UUID(sid) for sid in subgroup.song_ids])).all()
        song_name_map = {str(s.id): s.name for s in songs}
        
        results = []
        for song_id, ranks in song_ranks.items():
            if len(ranks) < 2:
                continue
            
            min_rank = min(ranks)
            max_rank = max(ranks)
            spread = max_rank - min_rank
            
            results.append({
                "song_id": song_id,
                "song_name": song_name_map.get(song_id, "Unknown"),
                "min_rank": round(min_rank, 1),
                "max_rank": round(max_rank, 1),
                "spread": round(spread, 1),
                "avg_rank": round(statistics.mean(ranks), 1)
            })

        return sorted(results, key=lambda x: x["spread"], reverse=True)

    @staticmethod
    def compute_top_bottom_consensus(
        franchise_id: str, subgroup_id: str, db: Session, limit: int = 10
    ) -> dict:
        """Find songs universally ranked high or low (low std dev)"""
        subgroup = db.query(Subgroup).filter_by(id=to_uuid(subgroup_id)).first()
        if not subgroup or not subgroup.song_ids:
            return {"top": [], "bottom": []}

        submissions = (
            db.query(Submission)
            .filter(
                Submission.franchise_id == to_uuid(franchise_id),
                Submission.submission_status == SubmissionStatus.VALID,
            )
            .all()
        )

        user_rel_rankings = []
        for sub in submissions:
            rel_map = RelativeRankingService.relativize(
                sub.parsed_rankings, 
                subgroup.song_ids
            )
            if rel_map:
                user_rel_rankings.append(rel_map)

        if not user_rel_rankings:
            return {"top": [], "bottom": []}

        song_ranks = defaultdict(list)
        for rel_map in user_rel_rankings:
            for song_id, rank in rel_map.items():
                song_ranks[song_id].append(rank)

        songs = db.query(Song).filter(Song.id.in_([UUID(sid) for sid in subgroup.song_ids])).all()
        song_name_map = {str(s.id): s.name for s in songs}
        
        # Calculate consistency for each song
        song_data = []
        for song_id, ranks in song_ranks.items():
            if len(ranks) < 2:
                continue
            
            avg = statistics.mean(ranks)
            std_dev = statistics.stdev(ranks)
            
            song_data.append({
                "song_id": song_id,
                "song_name": song_name_map.get(song_id, "Unknown"),
                "avg_rank": round(avg, 1),
                "std_dev": round(std_dev, 2),
                "consistency": round(1 / (1 + std_dev), 3)  # Higher = more agreement
            })

        # Sort by average and filter by consistency
        top_candidates = sorted([s for s in song_data if s["avg_rank"] <= 50], 
                               key=lambda x: (x["avg_rank"], -x["consistency"]))
        bottom_candidates = sorted([s for s in song_data if s["avg_rank"] >= 50], 
                                  key=lambda x: (-x["avg_rank"], -x["consistency"]))

        return {
            "top": top_candidates[:limit],
            "bottom": bottom_candidates[:limit]
        }

    @staticmethod
    def compute_outlier_users(
        franchise_id: str, subgroup_id: str, db: Session
    ) -> list[dict]:
        """Identify users with the most extreme rankings"""
        subgroup = db.query(Subgroup).filter_by(id=to_uuid(subgroup_id)).first()
        if not subgroup or not subgroup.song_ids:
            return []

        submissions = (
            db.query(Submission)
            .filter(
                Submission.franchise_id == to_uuid(franchise_id),
                Submission.submission_status == SubmissionStatus.VALID,
            )
            .all()
        )

        user_rel_rankings = {}
        for sub in submissions:
            rel_map = RelativeRankingService.relativize(
                sub.parsed_rankings, 
                subgroup.song_ids
            )
            if rel_map:
                user_rel_rankings[sub.username] = rel_map

        if not user_rel_rankings:
            return []

        # Calculate average ranks
        song_ranks = defaultdict(list)
        for rel_map in user_rel_rankings.values():
            for song_id, rank in rel_map.items():
                song_ranks[song_id].append(rank)

        song_averages = {
            sid: statistics.mean(ranks) for sid, ranks in song_ranks.items()
        }

        songs = db.query(Song).filter(Song.id.in_([UUID(sid) for sid in subgroup.song_ids])).all()
        song_name_map = {str(s.id): s.name for s in songs}

        # Calculate outlier score for each user
        results = []
        for username, rel_map in user_rel_rankings.items():
            deviations = []
            extreme_picks = []
            
            for song_id, user_rank in rel_map.items():
                avg_rank = song_averages.get(song_id)
                if avg_rank:
                    deviation = abs(user_rank - avg_rank)
                    deviations.append(deviation)
                    
                    if deviation > 30:  # Extreme deviation threshold
                        extreme_picks.append({
                            "song": song_name_map.get(song_id, "Unknown"),
                            "user_rank": round(user_rank, 1),
                            "avg_rank": round(avg_rank, 1),
                            "deviation": round(deviation, 1)
                        })
            
            if deviations:
                outlier_score = statistics.mean(deviations)
                results.append({
                    "username": username,
                    "outlier_score": round(outlier_score, 2),
                    "max_deviation": round(max(deviations), 1),
                    "extreme_picks": sorted(extreme_picks, key=lambda x: x["deviation"], reverse=True)[:5]
                })

        return sorted(results, key=lambda x: x["outlier_score"], reverse=True)

    @staticmethod
    def compute_comeback_songs(
        franchise_id: str, subgroup_id: str, db: Session
    ) -> list[dict]:
        """Identify sleeper/comeback songs - ranked very low by some, high by others"""
        subgroup = db.query(Subgroup).filter_by(id=to_uuid(subgroup_id)).first()
        if not subgroup or not subgroup.song_ids:
            return []

        submissions = (
            db.query(Submission)
            .filter(
                Submission.franchise_id == to_uuid(franchise_id),
                Submission.submission_status == SubmissionStatus.VALID,
            )
            .all()
        )

        user_rel_rankings = []
        for sub in submissions:
            rel_map = RelativeRankingService.relativize(
                sub.parsed_rankings, 
                subgroup.song_ids
            )
            if rel_map:
                user_rel_rankings.append(rel_map)

        if not user_rel_rankings:
            return []

        song_ranks = defaultdict(list)
        for rel_map in user_rel_rankings:
            for song_id, rank in rel_map.items():
                song_ranks[song_id].append(rank)

        songs = db.query(Song).filter(Song.id.in_([UUID(sid) for sid in subgroup.song_ids])).all()
        song_name_map = {str(s.id): s.name for s in songs}
        
        results = []
        for song_id, ranks in song_ranks.items():
            if len(ranks) < 3:
                continue
            
            sorted_ranks = sorted(ranks)
            bottom_third = sorted_ranks[:len(sorted_ranks)//3]
            top_third = sorted_ranks[-len(sorted_ranks)//3:]
            
            # A "comeback" song has some very low ranks AND some very high ranks
            if bottom_third and top_third:
                avg_bottom = statistics.mean(bottom_third)
                avg_top = statistics.mean(top_third)
                comeback_potential = avg_bottom - avg_top
                
                if comeback_potential > 30:  # Significant gap
                    results.append({
                        "song_id": song_id,
                        "song_name": song_name_map.get(song_id, "Unknown"),
                        "avg_low": round(avg_bottom, 1),
                        "avg_high": round(avg_top, 1),
                        "comeback_score": round(comeback_potential, 1),
                        "overall_avg": round(statistics.mean(ranks), 1)
                    })

        return sorted(results, key=lambda x: x["comeback_score"], reverse=True)

    @staticmethod
    def compute_subunit_popularity(
        franchise_id: str, db: Session
    ) -> list[dict]:
        """Aggregate rankings by subunit/artist to find strongest groups"""
        # Get all subunits for this franchise
        subgroups = db.query(Subgroup).filter_by(franchise_id=to_uuid(franchise_id)).all()
        
        submissions = (
            db.query(Submission)
            .filter(
                Submission.franchise_id == to_uuid(franchise_id),
                Submission.submission_status == SubmissionStatus.VALID,
            )
            .all()
        )

        if not submissions:
            return []

        results = []
        
        for subgroup in subgroups:
            if not subgroup.song_ids or len(subgroup.song_ids) < 1:
                continue
                
            # Calculate average rank for songs in this subunit
            all_ranks = []
            
            for sub in submissions:
                rel_map = RelativeRankingService.relativize(
                    sub.parsed_rankings,
                    subgroup.song_ids
                )
                if rel_map:
                    all_ranks.extend(rel_map.values())
            
            if all_ranks:
                avg_rank = statistics.mean(all_ranks)
                results.append({
                    "subgroup_name": subgroup.name,
                    "song_count": len(subgroup.song_ids),
                    "avg_rank": round(avg_rank, 2),
                    "total_rankings": len(all_ranks),
                    "is_subunit": getattr(subgroup, 'is_subunit', False)
                })

        return sorted(results, key=lambda x: x["avg_rank"])


class ControversyIndexService:
    @staticmethod
    def calculate(ranks: List[float]) -> Dict:
        if len(ranks) < 2:
            return {
                "std_dev": 0.0,
                "mean": round(statistics.mean(ranks), 2) if ranks else 0.0,
                "cv": 0.0,
                "iqr": 0.0,
                "bimodality_indicator": 1.0,
                "score": 0.0,
            }

        mean = statistics.mean(ranks)
        std_dev = statistics.stdev(ranks)
        cv = std_dev / mean if mean > 0.001 else 0
        sorted_ranks = sorted(ranks)
        n = len(sorted_ranks)
        q1 = sorted_ranks[int(n * 0.25)]
        q3 = sorted_ranks[int(n * 0.75)]
        iqr = q3 - q1
        bimodality_ratio = iqr / mean if mean > 0 else 0
        bimodality_indicator = 1.5 if bimodality_ratio > 0.3 else 1.0
        controversy_score = cv * bimodality_indicator

        return {
            "std_dev": round(std_dev, 2),
            "mean": round(mean, 2),
            "cv": round(cv, 4),
            "iqr": round(iqr, 2),
            "bimodality_indicator": bimodality_indicator,
            "score": round(controversy_score, 4),
        }
