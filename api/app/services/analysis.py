# app/services/analysis.py

import statistics
from collections import defaultdict
from typing import Dict, List
from uuid import UUID
import math

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

        # Fetch ALL valid submissions for this franchise
        submissions = (
            db.query(Submission)
            .filter(
                Submission.franchise_id == franchise_id,
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
        subgroup = db.query(Subgroup).filter_by(id=subgroup_id).first()
        if not subgroup or not subgroup.song_ids:
            return []

        submissions = (
            db.query(Submission)
            .filter(
                Submission.franchise_id == franchise_id,
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

        return sorted(results, key=lambda x: x["controversy_score"], reverse=True)

    @staticmethod
    def compute_hot_takes(
        franchise_id: str, subgroup_id: str, db: Session
    ) -> list[dict]:
        subgroup = db.query(Subgroup).filter_by(id=subgroup_id).first()
        if not subgroup or not subgroup.song_ids:
            return []

        submissions = (
            db.query(Submission)
            .filter(
                Submission.franchise_id == franchise_id,
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

        songs = db.query(Song).filter(Song.id.in_(subgroup.song_ids)).all()
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
        subgroups = db.query(Subgroup).filter_by(franchise_id=franchise_id).all()
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
                    Submission.franchise_id == franchise_id,
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
        subgroup = db.query(Subgroup).filter_by(id=subgroup_id).first()
        if not subgroup or not subgroup.song_ids:
            return []

        submissions = (
            db.query(Submission)
            .filter(
                Submission.franchise_id == franchise_id,
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

        songs = db.query(Song).filter(Song.id.in_(subgroup.song_ids)).all()
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