# app/seeds/import_rankings.py

import csv
import logging
import re
from pathlib import Path
from sqlalchemy.orm import Session
from app.models import Franchise, Subgroup, Song, Submission, SubmissionStatus
from app.services.tie_handling import TieHandlingService

logger = logging.getLogger(__name__)


class RankingsImporter:
    """Import user rankings from CSV file"""
    
    @staticmethod
    def parse_song_entry(entry: str) -> tuple[str, str]:
        """
        Parse a ranking entry like '1. Song Name - Artist'
        Returns (song_name, artist_name)
        """
        if not entry or entry.strip() == "":
            return None, None
            
        # Remove rank number (e.g., "1. ")
        entry = re.sub(r'^\d+\.\s*', '', entry.strip())
        
        # Split by ' - ' to separate song and artist
        parts = entry.split(' - ', 1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        return entry.strip(), None
    
    @staticmethod
    def import_from_csv(db: Session, csv_path: Path, franchise_name: str = "liella", subgroup_name: str = "All Songs"):
        """
        Import rankings from the wide-format CSV
        """
        try:
            if not csv_path.exists():
                logger.error(f"CSV file not found: {csv_path}")
                return 0
            
            # Get franchise and subgroup
            franchise = db.query(Franchise).filter_by(name=franchise_name).first()
            if not franchise:
                logger.error(f"Franchise '{franchise_name}' not found")
                return 0
            
            subgroup = db.query(Subgroup).filter(
                Subgroup.name == subgroup_name,
                Subgroup.franchise_id == franchise.id
            ).first()
            if not subgroup:
                logger.error(f"Subgroup '{subgroup_name}' not found")
                return 0
            
            # Build song name -> ID map with normalized keys
            songs = db.query(Song).filter_by(franchise_id=franchise.id).all()
            
            def normalize_name(name: str) -> str:
                """Normalize song name by replacing smart quotes and other variations"""
                # Replace smart/curly quotes with straight quotes
                # U+2018 (') and U+2019 (') -> straight apostrophe
                # U+201C (") and U+201D (") -> straight double quote
                name = name.replace('\u2018', "'").replace('\u2019', "'")
                name = name.replace('\u201c', '"').replace('\u201d', '"')
                return name.strip()
            
            song_by_name = {normalize_name(song.name): song.id for song in songs}
            # Also keep original names for exact matching
            for song in songs:
                song_by_name[song.name] = song.id
            
            logger.info(f"Loading rankings from {csv_path}")
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            if len(rows) < 2:
                logger.error("CSV file is empty or malformed")
                return 0
            
            # First row contains usernames
            header = rows[0]
            usernames = [h.strip() for h in header[1:] if h.strip()]  # Skip first column
            
            logger.info(f"Found {len(usernames)} users: {usernames}")
            
            # Initialize rankings dict for each user
            user_rankings = {username: {} for username in usernames}
            
            # Process each row (skip header and instruction row)
            for row_idx, row in enumerate(rows[1:], start=2):
                if len(row) < 2:
                    continue
                

                
                # Process each user's ranking for this position
                for col_idx, entry in enumerate(row[1:], start=1):
                    if col_idx > len(usernames):
                        break
                    
                    username = usernames[col_idx - 1]
                    song_name, artist = RankingsImporter.parse_song_entry(entry)
                    
                    if not song_name:
                        continue
                    
                    # Find song ID (try normalized name first, then exact match)
                    song_id = song_by_name.get(normalize_name(song_name)) or song_by_name.get(song_name)
                    if not song_id:
                        logger.debug(f"Song '{song_name}' not found in database for user {username}")
                        continue
                    
                    # Extract rank from entry
                    rank_match = re.match(r'^(\d+)\.', entry.strip())
                    if rank_match:
                        rank = int(rank_match.group(1))
                        user_rankings[username][str(song_id)] = rank
            
            # Create submissions for each user
            created_count = 0
            for username, rankings in user_rankings.items():
                if not rankings:
                    logger.warning(f"No rankings found for user {username}")
                    continue
                
                # Check if submission already exists
                existing = db.query(Submission).filter(
                    Submission.username == username,
                    Submission.franchise_id == franchise.id,
                    Submission.subgroup_id == subgroup.id
                ).first()
                
                if existing:
                    logger.info(f"Updating existing submission for {username}")
                    existing.parsed_rankings = rankings
                    existing.submission_status = SubmissionStatus.VALID
                else:
                    # Convert to mean ranks for ties
                    final_ranks = TieHandlingService.convert_tied_ranks(rankings)
                    
                    submission = Submission(
                        username=username,
                        franchise_id=franchise.id,
                        subgroup_id=subgroup.id,
                        raw_ranking_text=f"Imported from CSV - {len(rankings)} songs",
                        parsed_rankings=final_ranks,
                        submission_status=SubmissionStatus.VALID
                    )
                    db.add(submission)
                    created_count += 1
                    logger.info(f"Created submission for {username} with {len(rankings)} songs")
            
            db.commit()
            logger.info(f"✓ Successfully imported rankings for {created_count} users")
            return created_count
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to import rankings: {str(e)}")
            raise


def import_user_rankings(db: Session):
    """Main function to import user rankings"""
    csv_path = Path(__file__).parent / "user_rankings.csv"
    return RankingsImporter.import_from_csv(db, csv_path, "liella", "All Songs")
