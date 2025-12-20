# app/services/ranking_utils.py

from collections import defaultdict
from typing import Dict, List


class RelativeRankingService:
    """
    Handles the transformation of master rankings into relative 
    subgroup rankings (1..N).
    """

    @staticmethod
    def relativize(
        master_rankings: Dict[str, float], subgroup_song_ids: List[str]
    ) -> Dict[str, float]:
        """
        Filters master rankings to a subgroup and re-calculates 
        mean ranks for that subset.
        """
        # 1. Filter master rankings to only include songs in the subgroup
        subgroup_set = set(subgroup_song_ids)
        filtered_ranks = {
            sid: rank
            for sid, rank in master_rankings.items()
            if sid in subgroup_set
        }

        if not filtered_ranks:
            return {}

        # 2. Group songs by their original rank to preserve ties
        grouped = defaultdict(list)
        for song_id, original_rank in filtered_ranks.items():
            grouped[original_rank].append(song_id)

        # 3. Re-assign mean ranks based on subgroup positions
        result = {}
        current_position = 1

        # Sort by the original master rank to maintain the user's order
        for original_rank in sorted(grouped.keys()):
            tied_songs = grouped[original_rank]
            count = len(tied_songs)

            # Calculate the mean position for this tie group within the subgroup
            # e.g., if 2 songs are tied at the start, they occupy 1 and 2, mean = 1.5
            mean_rel_rank = (current_position + current_position + count - 1) / 2

            for song_id in tied_songs:
                result[song_id] = mean_rel_rank

            current_position += count

        return result