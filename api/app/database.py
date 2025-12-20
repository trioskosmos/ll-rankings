# app/database.py

import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import (
    OperationalError,
    IntegrityError,
    SQLAlchemyError
)
from app.config import settings
from app.models import Base
from app.exceptions import DatabaseException

logger = logging.getLogger(__name__)

engine = None
SessionLocal = None

def init_engine():
    """Initializes the SQLAlchemy engine with connection pooling.
    pool_pre_ping=True verifies connections before each query to
    prevent 'Server has gone away' errors during idle periods."""
    global engine, SessionLocal
    
    try:
        engine = create_engine(
            settings.database_url,
            echo=settings.database_echo,
            connect_args={
                "connect_timeout": 10  # PostgreSQL connection timeout (seconds)
            },
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600    # Recycle connections every hour
        )
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("✓ Database engine initialized successfully")
        return True
    
    except OperationalError as e:
        logger.error(f"✗ Cannot connect to database: {str(e)}")
        raise DatabaseException(f"Database connection failed: {str(e)}")
    
    except Exception as e:
        logger.error(f"✗ Unexpected database error: {str(e)}")
        raise DatabaseException(f"Database initialization failed: {str(e)}")


def get_db() -> Session:
    """FastAPI Dependency that yields a database session.
    Automatically closes the connection after the request finishes,
    performing a rollback if an unhandled exception occurs."""
    if SessionLocal is None:
        raise DatabaseException("Database not initialized. Call init_engine() first.")
    
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database operation failed: {str(e)}")
        db.rollback()
        raise DatabaseException(f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in database session: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Create all tables with error handling"""
    if engine is None:
        raise DatabaseException("Engine not initialized")
    
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created/verified")
        return True
    
    except Exception as e:
        logger.error(f"✗ Failed to create tables: {str(e)}")
        raise DatabaseException(f"Table creation failed: {str(e)}")


async def check_db_health() -> str:
    """Check database connectivity"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "healthy"
    except OperationalError:
        return "unhealthy: connection refused"
    except Exception as e:
        return f"unhealthy: {str(e)}"


def get_session():
    """Helper function to get a session (non-dependency context)"""
    if SessionLocal is None:
        raise DatabaseException("Database not initialized")
    return SessionLocal()