# app/services/ranking_utils.py

from collections import defaultdict
from typing import Dict, List


class RelativeRankingService:
    """
    Handles the transformation of master rankings into relative 
    subgroup rankings (1..N).
    """

    @staticmethod
    def relativize(master_rankings: Dict[str, float], subgroup_song_ids: List[str]) -> Dict[str, float]:
        # Filter to only existing songs in the subgroup
        subgroup_set = set(subgroup_song_ids)
        
        # Guard: Filter out any IDs that might be missing from master_rankings
        filtered_ranks = {
            sid: rank
            for sid, rank in master_rankings.items()
            if sid in subgroup_set
        }

        # Guard: If no songs from the subgroup are in this user's list, return empty
        if not filtered_ranks:
            return {}

        grouped = defaultdict(list)
        for song_id, original_rank in filtered_ranks.items():
            grouped[original_rank].append(song_id)

        result = {}
        current_position = 1
        for original_rank in sorted(grouped.keys()):
            tied_songs = grouped[original_rank]
            count = len(tied_songs)
            mean_rel_rank = (current_position + current_position + count - 1) / 2
            for song_id in tied_songs:
                result[song_id] = mean_rel_rank
            current_position += count

        return result