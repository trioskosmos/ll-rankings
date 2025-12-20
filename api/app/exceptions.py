# app/exceptions.py

class LiellaException(Exception):
    """Base exception for all Liella app errors"""
    pass

class DatabaseException(LiellaException):
    """Database connection/operation errors"""
    pass

class SeedingException(LiellaException):
    """Errors during database seeding"""
    pass

class ValidationException(LiellaException):
    """Data validation errors"""
    pass

class MatchingException(LiellaException):
    """Song matching errors"""
    pass

class DataIntegrityException(LiellaException):
    """Constraint violations, missing data, etc"""
    pass

class ConfigException(LiellaException):
    """Configuration/file loading errors"""
    pass