# app/services/matching.py

import re
import difflib
import logging
from typing import Tuple, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from app.models import Song, Franchise
from app.exceptions import MatchingException
from app.utils.validators import DataValidator

logger = logging.getLogger(__name__)

class StrictSongMatcher:
    """Match songs from ranking text strictly with error handling"""
    
    RANKING_PATTERN = re.compile(r"^\d+\.\s+(.+?)\s+-\s+.+$")
    
    @staticmethod
    def parse_ranking_text(
        text: str,
        franchise: str,
        db: Session
    ) -> Tuple[Dict[str, float], Dict[str, Dict]]:
        """
        Parse ranking text, match songs strictly.
        Returns:
            (matched: {song_id: rank}, conflicts: {song_name: reason_dict})
        """
        try:
            # Validate input
            DataValidator.validate_ranking_text(text)
            DataValidator.validate_franchise(franchise)
            
            lines = text.strip().split('\n')
            
            # Load songs for this franchise
            try:
                franchise_obj = db.query(Franchise).filter_by(name=franchise).first()
                if not franchise_obj:
                    raise MatchingException(f"Franchise '{franchise}' not found in database")
                
                songs = db.query(Song).filter_by(franchise_id=franchise_obj.id).all()
                if not songs:
                    raise MatchingException(f"No songs found for franchise '{franchise}'")
                
                logger.info(f"Matching against {len(songs)} songs for {franchise}")
            
            except MatchingException:
                raise
            except Exception as e:
                logger.error(f"Failed to load songs from database: {str(e)}")
                raise MatchingException(f"Database error: {str(e)}")
            
            song_by_name_lower = {song.name.lower(): song for song in songs}
            
            matched: Dict[str, float] = {}
            conflicts: Dict[str, Dict] = {}
            line_num = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                line_num += 1
                
                # Extract rank and song name
                regex_match = StrictSongMatcher.RANKING_PATTERN.match(line)
                if not regex_match:
                    conflicts[line] = {
                        "reason": "invalid_format",
                        "line_num": line_num,
                        "expected_format": "1. Song Name - Artist Info"
                    }
                    logger.debug(f"Line {line_num}: Invalid format - {line}")
                    continue
                
                song_name = regex_match.group(1).strip()
                rank = float(line_num)
                
                try:
                    DataValidator.validate_song_data(song_name, None)
                except Exception as e:
                    conflicts[song_name] = {
                        "reason": "invalid_song_name",
                        "line_num": line_num,
                        "error": str(e)
                    }
                    logger.warning(f"Line {line_num}: Invalid song name - {str(e)}")
                    continue
                
                # Strict match (case-insensitive)
                song = song_by_name_lower.get(song_name.lower())
                
                if song:
                    matched[str(song.id)] = rank
                    logger.debug(f"Line {line_num}: Matched '{song_name}'")
                else:
                    # Find suggestions
                    close = difflib.get_close_matches(
                        song_name.lower(),
                        song_by_name_lower.keys(),
                        n=3,
                        cutoff=0.75
                    )
                    
                    conflicts[song_name] = {
                        "reason": "not_found",
                        "line_num": line_num,
                        "suggestions": [song_by_name_lower[c].name for c in close] if close else []
                    }
                    logger.warning(f"Line {line_num}: No match for '{song_name}'")
            
            logger.info(f"Matching complete: {len(matched)} matched, {len(conflicts)} conflicts")
            return matched, conflicts
        
        except MatchingException:
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error during matching: {str(e)}")
            raise MatchingException(f"Matching failed: {str(e)}")