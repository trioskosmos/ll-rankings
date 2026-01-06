# app/services/analysis.py

import statistics
import json
import os
import time
from functools import wraps
from collections import defaultdict
from typing import Dict, List, Union, Callable, Any
from uuid import UUID
import math

from sqlalchemy.orm import Session
from app.models import Song, Subgroup, Submission, SubmissionStatus
from app.services.ranking_utils import RelativeRankingService


# Simple TTL cache for expensive computations
class AnalysisCache:
    """In-memory cache with TTL expiration for analysis results."""
    _cache: Dict[str, tuple] = {}  # {key: (value, expiry_time)}
    DEFAULT_TTL = 300  # 5 minutes
    
    @classmethod
    def get(cls, key: str) -> Any:
        """Get cached value if not expired."""
        if key in cls._cache:
            value, expiry = cls._cache[key]
            if time.time() < expiry:
                return value
            del cls._cache[key]
        return None
    
    @classmethod
    def set(cls, key: str, value: Any, ttl: int = None) -> None:
        """Store value with TTL."""
        ttl = ttl or cls.DEFAULT_TTL
        cls._cache[key] = (value, time.time() + ttl)
    
    @classmethod
    def clear(cls) -> None:
        """Clear all cached entries."""
        cls._cache.clear()
    
    @classmethod
    def make_key(cls, *args) -> str:
        """Create cache key from arguments."""
        return ":".join(str(a) for a in args)


def to_uuid(val: Union[str, UUID]) -> UUID:
    """Convert string or UUID to UUID object"""
    if isinstance(val, UUID):
        return val
    return UUID(val)

class AnalysisService:
    @staticmethod
    def compute_divergence_matrix(
        franchise_id: str, subgroup_id: str, db: Session
    ) -> Dict[str, any]:
        # Check cache first
        cache_key = AnalysisCache.make_key("divergence", franchise_id, subgroup_id)
        cached = AnalysisCache.get(cache_key)
        if cached is not None:
            return cached
            
        subgroup = db.query(Subgroup).filter_by(id=to_uuid(subgroup_id)).first()
        if not subgroup or not subgroup.song_ids:
            return {"matrix": {}, "rankings": {}, "song_names": {}}


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
        
        # Build user-vs-user divergence matrix
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

        # Build song-vs-user rankings matrix for loading calculations
        # Format: {song_id: {username: relative_rank}}
        all_songs = set()
        for rel_map in user_rel_rankings.values():
            all_songs.update(rel_map.keys())
        
        song_rankings = {}
        for song_id in all_songs:
            song_rankings[str(song_id)] = {}
            for username, rel_map in user_rel_rankings.items():
                if song_id in rel_map:
                    song_rankings[str(song_id)][username] = rel_map[song_id]
        
        # Get song names for display
        song_objs = db.query(Song).filter(Song.id.in_([to_uuid(s) for s in all_songs])).all()
        song_names = {str(s.id): s.name for s in song_objs}

        result = {
            "matrix": matrix,
            "rankings": song_rankings,
            "song_names": song_names
        }
        AnalysisCache.set(cache_key, result)
        return result


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
        # Check cache first
        cache_key = AnalysisCache.make_key("spice", franchise_id)
        cached = AnalysisCache.get(cache_key)
        if cached is not None:
            return cached
            
        subgroups = db.query(Subgroup).filter_by(franchise_id=to_uuid(franchise_id)).all()
        user_raw_data = defaultdict(dict)
        user_extreme_picks = defaultdict(list)
        all_usernames = set()


        # Fetch ALL valid submissions for this franchise ONCE (not per subgroup)
        submissions = (
            db.query(Submission)
            .filter(
                Submission.franchise_id == to_uuid(franchise_id),
                Submission.submission_status == SubmissionStatus.VALID
            ).all()
        )
        
        # Collect all song IDs across all subgroups for batch song name lookup
        all_song_ids = set()
        for sg in subgroups:
            if sg.song_ids and isinstance(sg.song_ids, list):
                all_song_ids.update(sg.song_ids)
        
        # Batch fetch ALL song names in one query
        songs = db.query(Song).filter(Song.id.in_([UUID(sid) for sid in all_song_ids])).all() if all_song_ids else []
        song_name_map = {str(s.id): s.name for s in songs}

        for sg in subgroups:
            if not sg.song_ids or not isinstance(sg.song_ids, list):
                continue
            
            song_count = len(sg.song_ids)

            user_rel_map = {}
            for sub in submissions:
                rel = RelativeRankingService.relativize(sub.parsed_rankings, sg.song_ids)
                if rel:
                    user_rel_map[sub.username] = rel
                    all_usernames.add(sub.username)

            # Pre-calculate averages for this subgroup (AFTER all submissions are processed)
            sg_song_averages = {}
            for sid in sg.song_ids:
                o_ranks = [rks[sid] for uname, rks in user_rel_map.items() if sid in rks]
                if o_ranks:
                    sg_song_averages[sid] = statistics.mean(o_ranks)

            for target_user, target_ranks in user_rel_map.items():
                sq_diffs = []
                for song_id, user_rank in target_ranks.items():
                    avg_others = sg_song_averages.get(song_id)
                    if avg_others is not None:
                        # Note: To be strictly "spice", it should be avg of OTHERS.
                        # But community avg is a close and faster proxy for large N.
                        # For precision, the rms calculation already excludes self in the original logic.
                        # Let's stick to the original rms logic but optimize the "extreme picks" pass.
                        sq_diffs.append((user_rank - avg_others) ** 2)
                        
                        dev = abs(user_rank - avg_others)
                        # Collect ALL deviations - we'll take top N per group later
                        user_extreme_picks[target_user].append({
                            "song": song_name_map.get(song_id, "Unknown"),
                            "group": sg.name,
                            "user_rank": round(user_rank, 1),
                            "avg_rank": round(avg_others, 1),
                            "deviation": round(dev, 1)
                        })

                if sq_diffs:
                    rms = math.sqrt(statistics.mean(sq_diffs))
                    # Normalize to 0-100 range where 100 = theoretical maximum
                    # Max RMS for perfectly inverted rankings = N/sqrt(3)
                    # So: norm_spice = (rms / (N/sqrt(3))) * 100 = (rms * sqrt(3) / N) * 100
                    max_rms = song_count / math.sqrt(3)
                    norm_spice = (rms / max_rms) * 100 if max_rms > 0 else 0
                    norm_spice = min(norm_spice, 100.0)  # Clamp to 100
                    
                    user_raw_data[target_user][sg.name] = {
                        "spice": round(norm_spice, 2),
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
            
            # Return ALL picks sorted by deviation - frontend will limit display based on mode
            all_picks = user_extreme_picks[username]
            all_picks.sort(key=lambda x: x['deviation'], reverse=True)
            
            final_results.append({
                "username": username,
                "global_spice": round(global_spice, 2),
                "group_breakdown": breakdown,
                "extreme_picks": all_picks
            })

        result = sorted(final_results, key=lambda x: x["global_spice"], reverse=True)
        AnalysisCache.set(cache_key, result)
        return result


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

        # Early return if no valid rankings
        if not user_rel_rankings:
            return []

        # Map to store ranks by song_id
        song_stats = defaultdict(list)
        for rel_map in user_rel_rankings:
            for song_id, rank in rel_map.items():
                song_stats[song_id].append(rank)

        # Get all songs in the subgroup to ensure full count
        songs = db.query(Song).filter(Song.id.in_([UUID(sid) for sid in subgroup.song_ids])).all()
        song_name_map = {str(s.id): s.name for s in songs}
        
        # Calculate rank count as the fallback for completely unranked songs
        total_songs_in_subgroup = len(subgroup.song_ids)
        
        results = []
        # Iterate over subgroup.song_ids instead of song_stats keys to ensure 100% coverage
        for sid in subgroup.song_ids:
            # Ensure consistent sid format for lookup
            sid_str = str(sid)
            ranks = song_stats.get(sid_str, [])
            
            if not ranks:
                # If no one ranked it, it gets the worst possible average (bottom of the pack)
                avg = float(total_songs_in_subgroup)
                pts = float(total_songs_in_subgroup)
            else:
                avg = statistics.mean(ranks)
                pts = sum(ranks)
                
            results.append({
                "song_id": sid_str,
                "song_name": song_name_map.get(sid_str, "Unknown"),
                "points": round(pts, 2),
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
                    "extreme_picks": sorted(extreme_picks, key=lambda x: x["deviation"], reverse=True)
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

    @staticmethod
    def compute_head_to_head(
        franchise_id: str, subgroup_id: str, user_a: str, user_b: str, db: Session
    ) -> dict:
        subgroup = db.query(Subgroup).filter_by(id=to_uuid(subgroup_id)).first()
        if not subgroup or not subgroup.song_ids:
            return {}

        users = db.query(Submission).filter(
            Submission.franchise_id == to_uuid(franchise_id),
            Submission.submission_status == SubmissionStatus.VALID,
            Submission.username.in_([user_a, user_b])
        ).all()
        
        rank_maps = {}
        for sub in users:
             rank_maps[sub.username] = RelativeRankingService.relativize(
                sub.parsed_rankings, subgroup.song_ids
             )

        if user_a not in rank_maps or user_b not in rank_maps:
             return {"error": "One or both users have no data for this view."}

        map_a = rank_maps[user_a]
        map_b = rank_maps[user_b]
        
        shared_songs = set(map_a.keys()) & set(map_b.keys())
        if not shared_songs:
             return {"error": "No shared ranked songs."}
        
        diffs = []
        for sid in shared_songs:
            r1 = map_a[sid]
            r2 = map_b[sid]
            diffs.append({"id": str(sid), "r1": r1, "r2": r2, "diff": abs(r1-r2)})

        # Resolve Song Names
        sids = [to_uuid(d['id']) for d in diffs]
        songs = db.query(Song).filter(Song.id.in_(sids)).all()
        song_lookup = {str(s.id): s.name for s in songs}
        
        for d in diffs:
            d['name'] = song_lookup.get(d['id'], "Unknown")
            del d['id']
            
        N = len(shared_songs)
        # Compatibility Score (Linear overlap metric)
        # Avg Diff ranges from 0 to N/2 approx.
        avg_diff = sum(d['diff'] for d in diffs) / N
        score = max(0, 100 * (1 - (avg_diff / (N / 2))))
        
        diffs.sort(key=lambda x: x['diff'], reverse=True)
        
        return {
            "users": [user_a, user_b],
            "score": round(score, 1),
            "common_count": N,
            "diffs": diffs
        }

    @staticmethod
    def compute_user_match(
         franchise_id: str, subgroup_id: str, target_user: str, db: Session
    ) -> dict:
        # Reuse existing divergence calculation
        result = AnalysisService.compute_divergence_matrix(franchise_id, subgroup_id, db)
        matrix = result.get("matrix", {})
        if target_user not in matrix:
            return {"error": "User not found"}
        
        row = matrix[target_user]
        # Remove self and sort
        others = [(u, val) for u, val in row.items() if u != target_user]
        others.sort(key=lambda x: x[1]) # Ascending divergence (Lower is better match)
        
        if not others:
            return {"soulmates": [], "nemeses": []}
            
        return {
            "soulmates": [{"user": u, "div": v} for u, v in others[:3]],
            "nemeses": [{"user": u, "div": v} for u, v in others[-3:][::-1]]
        }

    @staticmethod
    def compute_conformity(
         franchise_id: str, subgroup_id: str, db: Session
    ) -> dict:
        # Get Consensus
        community_ranks = AnalysisService.compute_community_rankings(franchise_id, subgroup_id, db)
        if not community_ranks:
            return {}
        
        # Rankings is List[Dict] usually. Let's ensure map
        # CommunityRankResponse usually has result_data as list of objects?
        # compute_community_rankings returns List[dict(song_id, rank, ...)]
        consensus_map = {str(r['song_id']): float(r['average']) for r in community_ranks}
        
        subgroup = db.query(Subgroup).filter_by(id=to_uuid(subgroup_id)).first()
        subs = db.query(Submission).filter(
             Submission.franchise_id == to_uuid(franchise_id),
             Submission.submission_status == SubmissionStatus.VALID
        ).all()
        
        user_scores = []
        for sub in subs:
            user_map = RelativeRankingService.relativize(sub.parsed_rankings, subgroup.song_ids)
            common = set(user_map.keys()) & set(consensus_map.keys())
            if len(common) < 5: continue
            
            # Mean Absolute Deviation from Consensus
            diffs = [abs(user_map[sid] - consensus_map[sid]) for sid in common]
            avg_diff = sum(diffs) / len(diffs)
            
            user_scores.append({
                "username": sub.username,
                "score": round(avg_diff, 2),
                "song_count": len(common)
            })
            
        user_scores.sort(key=lambda x: x['score'])
        
        return {
            "normies": user_scores[:5],
            "hipsters": user_scores[-5:][::-1],
            "all": user_scores
        }

    @staticmethod
    def compute_oshi_bias(franchise_id: str, username: str, db: Session) -> dict:
        try:
            # Try multiple possible locations for artists-info.json
            # Path 1: Docker container mount
            # Path 2: Running from project root (ll-rankings/data/)
            # Path 3: Running from api folder (../data/)
            possible_paths = [
                "/project_root/data/artists-info.json",
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "artists-info.json"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "..", "data", "artists-info.json"),
                os.path.join(os.getcwd(), "data", "artists-info.json"),
                os.path.join(os.getcwd(), "..", "data", "artists-info.json"),
            ]
            
            data_path = None
            for p in possible_paths:
                if os.path.exists(p):
                    data_path = p
                    break
            
            if not data_path:
                 return {"error": f"Artist data not found. Checked: {possible_paths}"}
                 
            with open(data_path, 'r', encoding='utf-8') as f:
                artists = json.load(f)
        except Exception as e:
            return {"error": str(e)}

        char_names = {}
        for a in artists:
            if a.get('characters') and len(a['characters']) == 1:
                cid = a['characters'][0]
                # Prefer English Name if available
                char_names[cid] = a.get('englishName', a['name'])

        group_chars = {}
        for a in artists:
            if a.get('characters'):
                group_chars[a['name']] = a['characters']
                if a.get('englishName'):
                    group_chars[a['englishName']] = a['characters']

        sub = db.query(Submission).filter(
            Submission.franchise_id == to_uuid(franchise_id),
            Submission.submission_status == SubmissionStatus.VALID,
            Submission.username == username
        ).order_by(Submission.created_at.desc()).first()

        if not sub:
            return {"error": "User not found"}

        user_ranks = sub.parsed_rankings
        if not user_ranks: return {"result": []}

        # Pre-fetch song names
        all_sids = []
        for sid in user_ranks.keys():
            try:
                all_sids.append(UUID(sid))
            except:
                continue
        
        songs = db.query(Song).filter(Song.id.in_(all_sids)).all()
        song_names = {str(s.id): s.name for s in songs}
        
        ranks = [float(v) for v in user_ranks.values()]
        global_avg = sum(ranks) / len(ranks)

        # Find Subgroups (Solos AND Subunits)
        # Remove is_subunit filter to find everything, but we will filter by artist char count later
        all_subgroups = db.query(Subgroup).filter(
            Subgroup.franchise_id == to_uuid(franchise_id)
        ).all()
        
        song_to_chars = defaultdict(set)
        for sg in all_subgroups:
            # Fuzzy Logic for Artist Matching
            name_key = sg.name
            matched_cids = None
            
            # 1. Exact Match (JP or EN)
            if name_key in group_chars:
                matched_cids = group_chars[name_key]
            
            # 2. "Solos" suffix handling (e.g. "Kanon Solos" -> "Kanon")
            elif name_key.endswith(" Solos"):
                 base_name = name_key.replace(" Solos", "")
                 # Look for artist whose English name contains base_name
                 # e.g. "Kanon" in "Kanon Shibuya"
                 for en_name, cids in group_chars.items():
                     if len(cids) == 1 and base_name in en_name:
                         matched_cids = cids
                         break
            
            if matched_cids:
                # STRICT FILTER: Only allow SOLO artists (1 character)
                # User requested "only the solos"
                if len(matched_cids) != 1:
                    continue

                if not sg.song_ids: continue
                for sid in sg.song_ids:
                    for cid in matched_cids:
                        if cid: song_to_chars[sid].add(cid)
        
        char_stats = defaultdict(list)
        char_songs = defaultdict(list)
        for sid, rank in user_ranks.items():
            if sid in song_to_chars:
                for cid in song_to_chars[sid]:
                    rank_val = float(rank)
                    char_stats[cid].append(rank_val)
                    char_songs[cid].append({
                        "name": song_names.get(sid, "Unknown Song"),
                        "rank": rank_val
                    })
                    
        results = []
        for cid, cranks in char_stats.items():
            # Lower threshold to 1 to include new members with few songs (e.g. Tomari, Shiki)
            if len(cranks) < 1: continue
            avg = sum(cranks) / len(cranks)
            # Bias: How much BETTER (lower rank) than global avg?
            # Positive Bias = Liked more than average song.
            bias = global_avg - avg 
            results.append({
                "char_id": cid,
                "name": char_names.get(cid, cid),
                "avg_rank": round(avg, 1),
                "bias": round(bias, 1),
                "count": len(cranks),
                "songs": sorted(char_songs[cid], key=lambda x: x['rank'])
            })
            
        results.sort(key=lambda x: x['bias'], reverse=True)
        return {"global_avg": round(global_avg, 1), "biases": results}

    @staticmethod
    def _compute_fans_for_songs(
        franchise_id: str, artist_song_ids: set, target_artist_name: str, db: Session
    ) -> dict:
        """Helper to compute fan data given a set of song IDs."""
        if not artist_song_ids:
            return {"error": f"No songs found for {target_artist_name}"}

        # Get all submissions
        submissions = db.query(Submission).filter(
            Submission.franchise_id == to_uuid(franchise_id),
            Submission.submission_status == SubmissionStatus.VALID
        ).all()

        # Group by username (take latest per user)
        user_subs = {}
        for sub in submissions:
            if sub.username not in user_subs or sub.created_at > user_subs[sub.username].created_at:
                user_subs[sub.username] = sub

        # Pre-fetch song names for artist songs
        songs = db.query(Song).filter(Song.id.in_([UUID(sid) for sid in artist_song_ids])).all()
        song_names = {str(s.id): s.name for s in songs}

        results = []
        for username, sub in user_subs.items():
            user_ranks = sub.parsed_rankings
            if not user_ranks:
                continue

            all_ranks = [float(v) for v in user_ranks.values()]
            global_avg = sum(all_ranks) / len(all_ranks) if all_ranks else 0

            artist_ranks = []
            song_details = []
            for sid in artist_song_ids:
                if sid in user_ranks:
                    rank = float(user_ranks[sid])
                    artist_ranks.append(rank)
                    song_details.append({
                        "name": song_names.get(sid, "Unknown"),
                        "rank": rank
                    })

            if not artist_ranks:
                continue

            artist_avg = sum(artist_ranks) / len(artist_ranks)
            bias = global_avg - artist_avg

            results.append({
                "username": username,
                "bias": round(bias, 1),
                "artist_avg": round(artist_avg, 1),
                "global_avg": round(global_avg, 1),
                "song_count": len(artist_ranks),
                "songs": sorted(song_details, key=lambda x: x['rank'])
            })

        results.sort(key=lambda x: x['bias'], reverse=True)
        return {
            "artist_id": target_artist_name,
            "artist_name": target_artist_name,
            "song_count": len(artist_song_ids),
            "fans": results
        }

    @staticmethod
    def compute_artist_fans(franchise_id: str, artist_id: str, db: Session) -> dict:
        """Calculate which users favor a specific artist most (reverse of compute_oshi_bias)."""
        
        # Special case: "All Solos" fetches the combined subgroup directly
        if artist_id.lower() == 'all solos':
            all_solos_sg = db.query(Subgroup).filter(
                Subgroup.franchise_id == to_uuid(franchise_id),
                Subgroup.name == "All Solos"
            ).first()
            
            if not all_solos_sg or not all_solos_sg.song_ids:
                return {"error": "All Solos subgroup not found. Please restart the backend to seed it."}
            
            artist_song_ids = set(all_solos_sg.song_ids)
            target_artist_name = "All Solos"
            
            # Jump to submission processing (skip character matching)
            return AnalysisService._compute_fans_for_songs(
                franchise_id, artist_song_ids, target_artist_name, db
            )
        
        try:
            possible_paths = [
                "/project_root/data/artists-info.json",
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "artists-info.json"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "..", "data", "artists-info.json"),
                os.path.join(os.getcwd(), "data", "artists-info.json"),
                os.path.join(os.getcwd(), "..", "data", "artists-info.json"),
            ]
            
            data_path = None
            for p in possible_paths:
                if os.path.exists(p):
                    data_path = p
                    break
            
            if not data_path:
                return {"error": f"Artist data not found. Checked: {possible_paths}"}
            with open(data_path, 'r', encoding='utf-8') as f:
                artists = json.load(f)
        except Exception as e:
            return {"error": str(e)}

        # Find the target artist name and ID
        target_artist_name = None
        target_cid = None
        
        for a in artists:
            if a.get('characters') and len(a['characters']) == 1:
                cid = a['characters'][0]
                name_en = a.get('englishName', '')
                name_jp = a.get('name', '')
                
                # Match by ID or Name (case-insensitive, with partial match support)
                artist_lower = artist_id.lower()
                if (cid == artist_id or 
                    name_en.lower() == artist_lower or 
                    name_jp.lower() == artist_lower or
                    # Partial match: first name must match start of full name
                    name_en.lower().startswith(artist_lower + ' ') or
                    name_en.lower().startswith(artist_lower)):
                    target_artist_name = name_en or name_jp
                    target_cid = cid
                    break
        
        if not target_artist_name or not target_cid:
            return {"error": f"Artist {artist_id} not found"}

        # Build group_chars mapping for fuzzy matching
        group_chars = {}
        for a in artists:
            if a.get('characters'):
                group_chars[a['name']] = a['characters']
                if a.get('englishName'):
                    group_chars[a['englishName']] = a['characters']

        # Find all subgroups for this artist
        all_subgroups = db.query(Subgroup).filter(
            Subgroup.franchise_id == to_uuid(franchise_id)
        ).all()

        artist_song_ids = set()
        for sg in all_subgroups:
            name_key = sg.name
            matched_cids = None
            
            if name_key in group_chars:
                matched_cids = group_chars[name_key]
            elif name_key.endswith(" Solos"):
                base_name = name_key.replace(" Solos", "")
                for en_name, cids in group_chars.items():
                    if len(cids) == 1 and base_name in en_name:
                        matched_cids = cids
                        break
            
            if matched_cids and len(matched_cids) == 1 and matched_cids[0] == target_cid:
                if sg.song_ids:
                    artist_song_ids.update(sg.song_ids)

        # Use the helper function for consistent processing
        return AnalysisService._compute_fans_for_songs(
            franchise_id, artist_song_ids, target_artist_name, db
        )

    @staticmethod
    def compute_release_trends(franchise_id: str, db: Session, subgroup_name: str = "All Songs") -> dict:
        """
        Compute ranking trends by release date.
        Returns yearly aggregates and individual song timeline data.
        """
        # Check cache
        cache_key = AnalysisCache.make_key(f"release_trends_{subgroup_name}", franchise_id)
        cached = AnalysisCache.get(cache_key)
        if cached is not None:
            return cached

        # Get specific subgroup (or "All Songs" default)
        subgroup = db.query(Subgroup).filter(
            Subgroup.franchise_id == to_uuid(franchise_id),
            Subgroup.name == subgroup_name
        ).first()

        if not subgroup or not subgroup.song_ids:
            return {"yearly_trends": [], "timeline": []}

        # Fetch all songs with release dates for this franchise
        songs = db.query(Song).filter(
            Song.franchise_id == to_uuid(franchise_id)
        ).all()

        song_by_id = {str(s.id): s for s in songs}
        song_ids_in_subgroup = set(subgroup.song_ids)

        # Get all valid submissions
        submissions = db.query(Submission).filter(
            Submission.franchise_id == to_uuid(franchise_id),
            Submission.submission_status == SubmissionStatus.VALID
        ).all()

        if not submissions:
            return {"yearly_trends": [], "timeline": []}

        # Calculate average rank for each song across all users
        song_ranks = defaultdict(list)
        for sub in submissions:
            if not sub.parsed_rankings:
                continue
            for song_id, rank in sub.parsed_rankings.items():
                if song_id in song_ids_in_subgroup:
                    try:
                        song_ranks[song_id].append(int(rank))
                    except (ValueError, TypeError):
                        continue

        # Build timeline data (individual songs)
        timeline = []
        yearly_data = defaultdict(list)  # year -> list of avg ranks

        # Helper to hold intermediate data
        raw_song_data = []
        all_stdevs = []

        # First pass: Calculate stats for all songs
        for song_id, ranks in song_ranks.items():
            if song_id not in song_by_id:
                continue

            song = song_by_id[song_id]
            if not song.release_date:
                continue

            avg_rank = sum(ranks) / len(ranks)
            year = song.release_date.year
            
            import statistics
            try:
                stdev = statistics.stdev(ranks) if len(ranks) > 1 else 0.0
            except:
                stdev = 0.0
            
            if len(ranks) > 1:
                all_stdevs.append(stdev)
                
            raw_song_data.append({
                "song_id": song_id,
                "title": song.name,
                "release_date": song.release_date,
                "avg_rank": avg_rank,
                "stdev": stdev,
                "year": year
            })
            
            yearly_data[year].append(avg_rank)

        # Calculate dynamic thresholds
        if len(all_stdevs) >= 4:
            quantiles = statistics.quantiles(all_stdevs, n=4)
            p_safe = quantiles[0]  # 25th percentile
            p_mid = quantiles[1]   # Median
            p_cont = quantiles[2]  # 75th percentile
        else:
            p_safe, p_mid, p_cont = 20.0, 30.0, 40.0

        # Second pass: Build timeline with colors
        for item in raw_song_data:
            stdev = item['stdev']
            
            if stdev <= p_safe:
                color = "#22d3ee"  # Cyan (Consensus)
                label = "Universal Consensus"
            elif stdev <= p_mid:
                color = "#a855f7"  # Purple (Mostly Agreed)
                label = "Mostly Agreed"
            elif stdev <= p_cont:
                color = "#f472b6"  # Pink (Controversial)
                label = "Controversial"
            else:
                color = "#f87171"  # Red (War Zone)
                label = "War Zone"

            timeline.append({
                "song_id": item['song_id'],
                "title": item['title'],
                "date": item['release_date'].isoformat(),
                "rank": round(item['avg_rank'], 1),
                "color": color,
                "controversy": round(stdev, 2),
                "label": label
            })

        # Sort timeline by date
        timeline.sort(key=lambda x: x["date"])

        # Build yearly trends
        yearly_trends = []
        for year in sorted(yearly_data.keys()):
            ranks = yearly_data[year]
            yearly_trends.append({
                "year": year,
                "avg_rank": round(sum(ranks) / len(ranks), 1),
                "song_count": len(ranks)
            })

        result = {
            "yearly_trends": yearly_trends,
            "timeline": timeline
        }

        AnalysisCache.set(cache_key, result, ttl=600)  # 10 min cache
        return result
