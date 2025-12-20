# app/services/matching.py

import difflib
import re
from typing import Dict, Tuple

from sqlalchemy.orm import Session

from app.models import Franchise, Song


class StrictSongMatcher:
    # Format: "Rank. Song Name - Artist Info"
    RANKING_PATTERN = re.compile(r"^(\d+)\.\s+(.+?)\s+-\s+(.+)$")

    @staticmethod
    def _normalize(text: str) -> str:
        """Standardize special characters and case for robust matching."""
        if not text:
            return ""
        return (
            text.strip()
            .lower()
            .replace("’", "'")  # Curly apostrophe
            .replace("‘", "'")  # Curly apostrophe
            .replace("–", "-")  # En-dash
            .replace("—", "-")  # Em-dash
        )

    @staticmethod
    def parse_ranking_text(
        text: str, franchise: str, db: Session
    ) -> Tuple[Dict[str, float], Dict[str, dict]]:
        # Load franchise and associated songs
        franchise_obj = db.query(Franchise).filter_by(name=franchise).first()
        songs = db.query(Song).filter_by(franchise_id=franchise_obj.id).all()

        # Build normalized lookup map: {normalized_name: SongObject}
        song_lookup = {StrictSongMatcher._normalize(s.name): s for s in songs}

        matched: Dict[str, float] = {}
        conflicts: Dict[str, dict] = {}
        seen_song_ids = set()

        lines = [l.strip() for l in text.strip().split("\n") if l.strip()]

        for idx, line in enumerate(lines, start=1):
            match = StrictSongMatcher.RANKING_PATTERN.match(line)

            # Error 1: Format mismatch
            if not match:
                conflicts[f"line_{idx}"] = {
                    "reason": "invalid_format",
                    "line_num": idx,
                    "raw_text": line,
                    "expected_format": "Rank. Song Name - Artist Info",
                }
                continue

            rank_str, song_name, _ = match.groups()
            song_name_clean = song_name.strip()
            normalized_input = StrictSongMatcher._normalize(song_name_clean)

            # Error 2: Song lookup (using normalized strings)
            song = song_lookup.get(normalized_input)

            if not song:
                # Fuzzy suggestions using normalized keys but returning original names
                close_matches = difflib.get_close_matches(
                    normalized_input, song_lookup.keys(), n=3, cutoff=0.7
                )
                conflicts[song_name_clean] = {
                    "reason": "song_not_found",
                    "line_num": idx,
                    "raw_text": line,
                    "suggestions": [song_lookup[c].name for c in close_matches],
                }
                continue

            # Error 3: Duplicate in the current list
            if str(song.id) in seen_song_ids:
                conflicts[f"{song_name_clean}_dup_{idx}"] = {
                    "reason": "duplicate_song",
                    "line_num": idx,
                    "raw_text": line,
                }
                continue

            # Success
            matched[str(song.id)] = float(rank_str)
            seen_song_ids.add(str(song.id))

        return matched, conflicts