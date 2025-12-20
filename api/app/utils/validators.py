# app/utils/validators.py

import logging
import re
from typing import Optional
from app.exceptions import ValidationException

logger = logging.getLogger(__name__)

class DataValidator:
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format"""
        if not username or not isinstance(username, str):
            raise ValidationException("Username must be a non-empty string")
        
        username = username.strip()
        if len(username) < 2:
            raise ValidationException("Username must be at least 2 characters")
        
        if len(username) > 100:
            raise ValidationException("Username must be less than 100 characters")
        
        return True
    
    @staticmethod
    def validate_franchise(franchise: str) -> bool:
        """Validate franchise name"""
        valid_franchises = ["liella", "u's", "aqours", "nijigasaki", "hasunosora"]
        
        if not franchise or not isinstance(franchise, str):
            raise ValidationException("Franchise must be a non-empty string")
        
        franchise_lower = franchise.lower().strip()
        if franchise_lower not in valid_franchises:
            raise ValidationException(
                f"Invalid franchise. Choose from: {', '.join(valid_franchises)}"
            )
        
        return True
    
    @staticmethod
    def validate_ranking_text(text: str) -> bool:
        """Validate ranking text format"""
        if not text or not isinstance(text, str):
            raise ValidationException("Ranking text must be non-empty")
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        if len(lines) == 0:
            raise ValidationException("Ranking text appears empty")
        
        if len(lines) < 3:
            raise ValidationException("Need at least 3 songs to rank")
        
        if len(lines) > 500:
            raise ValidationException("Too many rankings (max 500)")
        
        return True
    
    @staticmethod
    def validate_song_data(name: Optional[str], url: Optional[str]) -> bool:
        """Validate individual song data"""
        if not name or not isinstance(name, str):
            raise ValidationException("Song name must be non-empty string")
        
        name = name.strip()
        if len(name) == 0:
            raise ValidationException("Song name cannot be empty")
        
        if len(name) > 500:
            raise ValidationException("Song name too long (max 500 chars)")
        
        if url:
            url = str(url).strip()
            if len(url) > 2000:
                raise ValidationException("YouTube URL too long")
        
        return True