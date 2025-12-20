# app/seeds/init.py

import json
import logging
import tomllib
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.models import Franchise, Song, Subgroup
from app.exceptions import SeedingException, ConfigException, DataIntegrityException

logger = logging.getLogger(__name__)

class DatabaseSeeder:
    
    @staticmethod
    def load_songs_json(franchise_name: str = "liella") -> list[dict]:
        """Load songs from JSON file with error handling"""
        try:
            seed_path = Path(__file__).parent / "liella_songs.json"
            
            if not seed_path.exists():
                raise ConfigException(f"Songs JSON file not found: {seed_path}")
            
            with open(seed_path, 'r', encoding='utf-8') as f:
                songs = json.load(f)
            
            if not isinstance(songs, list):
                raise ConfigException("Songs JSON must be a list")
            
            if len(songs) == 0:
                raise ConfigException("Songs JSON is empty")
            
            logger.info(f"✓ Loaded {len(songs)} songs from JSON")
            return songs
        
        except json.JSONDecodeError as e:
            logger.error(f"✗ Invalid JSON format: {str(e)}")
            raise ConfigException(f"Songs JSON is malformed: {str(e)}")
        
        except ConfigException:
            raise
        
        except Exception as e:
            logger.error(f"✗ Unexpected error loading songs: {str(e)}")
            raise SeedingException(f"Failed to load songs: {str(e)}")
    
    @staticmethod
    def load_subgroups_toml() -> dict:
        """Load subgroups from TOML file with error handling"""
        try:
            toml_path = Path(__file__).parent / "subgroups.toml"
            
            if not toml_path.exists():
                raise ConfigException(f"Subgroups TOML file not found: {toml_path}")
            
            with open(toml_path, 'rb') as f:
                config = tomllib.load(f)
            
            if not isinstance(config, dict):
                raise ConfigException("Subgroups TOML must be a dictionary")
            
            if len(config) == 0:
                raise ConfigException("Subgroups TOML is empty")
            
            logger.info(f"✓ Loaded TOML with {len(config)} franchises")
            return config
        
        except tomllib.TOMLDecodeError as e:
            logger.error(f"✗ Invalid TOML format: {str(e)}")
            raise ConfigException(f"Subgroups TOML is malformed: {str(e)}")
        
        except ConfigException:
            raise
        
        except Exception as e:
            logger.error(f"✗ Unexpected error loading TOML: {str(e)}")
            raise SeedingException(f"Failed to load subgroups: {str(e)}")
    
    @staticmethod
    def seed_franchises(db: Session):
        """Create franchise records with error handling"""
        franchises = ["liella", "u's", "aqours", "nijigasaki", "hasunosora"]
        created = 0
        
        try:
            for franchise_name in franchises:
                try:
                    existing = db.query(Franchise).filter_by(name=franchise_name).first()
                    if not existing:
                        franchise = Franchise(name=franchise_name)
                        db.add(franchise)
                        created += 1
                    else:
                        logger.info(f"  Franchise '{franchise_name}' already exists")
                
                except IntegrityError as e:
                    db.rollback()
                    logger.warning(f"  Duplicate franchise '{franchise_name}': {str(e)}")
                
                except Exception as e:
                    db.rollback()
                    raise DataIntegrityException(f"Failed to add franchise '{franchise_name}': {str(e)}")
            
            db.commit()
            logger.info(f"✓ Created {created} new franchises (total: {len(franchises)})")
            return created
        
        except DataIntegrityException:
            raise
        
        except Exception as e:
            db.rollback()
            logger.error(f"✗ Failed to seed franchises: {str(e)}")
            raise SeedingException(f"Franchise seeding failed: {str(e)}")
    
    @staticmethod
    def seed_songs(db: Session, franchise_name: str = "liella"):
        """Load songs from JSON into database with error handling"""
        try:
            franchise = db.query(Franchise).filter_by(name=franchise_name).first()
            if not franchise:
                raise DataIntegrityException(f"Franchise '{franchise_name}' not found. Run seed_franchises first.")
            
            songs_data = DatabaseSeeder.load_songs_json(franchise_name)
            
            created_count = 0
            skipped_count = 0
            
            for idx, song_data in enumerate(songs_data):
                try:
                    # Validate song data
                    if not song_data.get("name"):
                        logger.warning(f"  Song {idx}: Missing 'name' field. Skipping.")
                        skipped_count += 1
                        continue
                    
                    song_name = str(song_data["name"]).strip()
                    if not song_name:
                        logger.warning(f"  Song {idx}: Empty name. Skipping.")
                        skipped_count += 1
                        continue
                    
                    youtube_url = song_data.get("youtube_url")
                    if youtube_url:
                        youtube_url = str(youtube_url).strip() or None
                    
                    # Check if already exists
                    existing = db.query(Song).filter(
                        Song.name == song_name,
                        Song.franchise_id == franchise.id
                    ).first()
                    
                    if not existing:
                        song = Song(
                            name=song_name,
                            youtube_url=youtube_url,
                            franchise_id=franchise.id
                        )
                        db.add(song)
                        created_count += 1
                    else:
                        logger.debug(f"  Song '{song_name}' already exists")
                
                except IntegrityError as e:
                    db.rollback()
                    logger.warning(f"  Integrity error for song {idx}: {str(e)}")
                    skipped_count += 1
                
                except Exception as e:
                    db.rollback()
                    logger.error(f"  Error processing song {idx}: {str(e)}")
                    skipped_count += 1
            
            db.commit()
            logger.info(f"✓ Created {created_count} songs for {franchise_name} (skipped: {skipped_count})")
            
            if created_count == 0:
                logger.warning(f"⚠ No new songs created for {franchise_name}")
            
            return created_count
        
        except DataIntegrityException:
            raise
        
        except Exception as e:
            db.rollback()
            logger.error(f"✗ Failed to seed songs: {str(e)}")
            raise SeedingException(f"Song seeding failed: {str(e)}")
    
    @staticmethod
    def seed_subgroups(db: Session, franchise_name: str = "liella"):
        """Load subgroups from TOML with error handling"""
        try:
            franchise = db.query(Franchise).filter_by(name=franchise_name).first()
            if not franchise:
                raise DataIntegrityException(f"Franchise '{franchise_name}' not found")
            
            config = DatabaseSeeder.load_subgroups_toml()
            franchise_config = config.get(franchise_name, {})
            
            if not franchise_config:
                logger.warning(f"⚠ No configuration found for franchise '{franchise_name}' in TOML")
                return 0
            
            # Build song name -> UUID map
            songs = db.query(Song).filter_by(franchise_id=franchise.id).all()
            song_by_name = {song.name: song.id for song in songs}
            
            created_count = 0
            
            for subgroup_key, subgroup_cfg in franchise_config.items():
                try:
                    if not isinstance(subgroup_cfg, dict) or "songs" not in subgroup_cfg:
                        logger.debug(f"  Skipping non-subgroup config: {subgroup_key}")
                        continue
                    
                    subgroup_name = subgroup_cfg.get("name", "").strip()
                    if not subgroup_name:
                        logger.warning(f"  Subgroup {subgroup_key}: Missing name. Skipping.")
                        continue
                    
                    is_custom = subgroup_cfg.get("is_custom", False)
                    song_names = subgroup_cfg.get("songs", [])
                    
                    if not isinstance(song_names, list):
                        logger.error(f"  Subgroup '{subgroup_name}': songs must be a list. Skipping.")
                        continue
                    
                    # Match song names to IDs
                    song_ids = []
                    unmatched = []
                    
                    for song_name in song_names:
                        song_name = str(song_name).strip()
                        if not song_name:
                            continue
                        
                        if song_name in song_by_name:
                            song_ids.append(str(song_by_name[song_name]))
                        else:
                            unmatched.append(song_name)
                    
                    if unmatched:
                        logger.warning(f"  Subgroup '{subgroup_name}': {len(unmatched)} songs not found: {unmatched[:3]}")
                    
                    if not song_ids:
                        logger.error(f"  Subgroup '{subgroup_name}': No songs matched. Skipping.")
                        continue
                    
                    # Upsert subgroup
                    existing = db.query(Subgroup).filter(
                        Subgroup.name == subgroup_name,
                        Subgroup.franchise_id == franchise.id
                    ).first()
                    
                    try:
                        if existing:
                            existing.song_ids = song_ids
                            existing.is_custom = is_custom
                            logger.info(f"  Updated subgroup '{subgroup_name}' with {len(song_ids)} songs")
                        else:
                            new_subgroup = Subgroup(
                                name=subgroup_name,
                                franchise_id=franchise.id,
                                song_ids=song_ids,
                                is_custom=is_custom
                            )
                            db.add(new_subgroup)
                            created_count += 1
                            logger.info(f"  Created subgroup '{subgroup_name}' with {len(song_ids)} songs")
                        
                        db.commit()
                    
                    except IntegrityError as e:
                        db.rollback()
                        logger.error(f"  Integrity error for subgroup '{subgroup_name}': {str(e)}")
                
                except Exception as e:
                    db.rollback()
                    logger.error(f"  Unexpected error for subgroup '{subgroup_key}': {str(e)}")
                    continue
            
            logger.info(f"✓ Created {created_count} subgroups for {franchise_name}")
            return created_count
        
        except DataIntegrityException:
            raise
        
        except Exception as e:
            db.rollback()
            logger.error(f"✗ Failed to seed subgroups: {str(e)}")
            raise SeedingException(f"Subgroup seeding failed: {str(e)}")
    
    @staticmethod
    def seed_all(db: Session):
        """Run all seeds with error handling"""
        logger.info("\n" + "="*50)
        logger.info("🌱 Starting database seeding...")
        logger.info("="*50 + "\n")
        
        try:
            DatabaseSeeder.seed_franchises(db)
            DatabaseSeeder.seed_songs(db, "liella")
            DatabaseSeeder.seed_subgroups(db, "liella")
            
            logger.info("\n" + "="*50)
            logger.info("✓ Seeding complete!")
            logger.info("="*50 + "\n")
            
            return True
        
        except (SeedingException, ConfigException, DataIntegrityException) as e:
            logger.error(f"\n✗ SEEDING FAILED: {str(e)}\n")
            raise
        
        except Exception as e:
            logger.error(f"\n✗ UNEXPECTED ERROR: {str(e)}\n")
            raise SeedingException(f"Seeding failed: {str(e)}")