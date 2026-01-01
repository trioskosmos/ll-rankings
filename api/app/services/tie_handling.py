from collections import defaultdict
from typing import Dict


class TieHandlingService:
    """Convert tied ranks to mean ranks"""

    @staticmethod
    def convert_tied_ranks(rankings: Dict[str, float]) -> Dict[str, float]:
        """
        Convert rankings with ties to mean ranks.

        Example:
            {song1: 1, song2: 1, song3: 3} -> {song1: 1.5, song2: 1.5, song3: 3}
        """
        # Group by rank
        grouped = defaultdict(list)
        for song_id, rank in rankings.items():
            grouped[rank].append(song_id)

        # Calculate mean ranks
        result = {}
        position = 1

        for rank in sorted(grouped.keys()):
            songs = grouped[rank]
            count = len(songs)

            # Mean of positions they occupy
            # e.g., 3 songs at position 1 occupy positions 1-3, mean = 2
            mean_rank = (position + position + count - 1) / 2

            for song_id in songs:
                result[song_id] = mean_rank

            position += count

        return result
