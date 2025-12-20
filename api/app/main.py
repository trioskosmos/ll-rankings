# app/main.py

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app import database  # Import module, not individual exports
from app.seeds.init import DatabaseSeeder
from app.exceptions import LiellaException
from app.logging_config import setup_logging
from app.api.v1 import submissions, analysis, health
from app.jobs import analysis_scheduler

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        logger.info("Starting application...")
        database.init_engine()
        database.init_db()
        
        db = database.get_session()
        try:
            from app.models import Song
            song_count = db.query(Song).count()
            
            # Initial setup for songs (only if empty)
            if song_count == 0:
                logger.info("Database empty, running initial song seeds...")
                DatabaseSeeder.seed_franchises(db)
                DatabaseSeeder.seed_songs(db, "liella")
            
            # SUBGROUP SYNCHRONIZATION
            # This runs every time the app starts/reloads
            logger.info("Synchronizing subgroups from TOML...")
            DatabaseSeeder.seed_subgroups(db, "liella")
            
            logger.info(f"Ready: {song_count} songs in database.")
            
        except Exception as e:
            logger.error(f"Seeding error: {str(e)}")
            db.close()
            raise
        finally:
            db.close()
        
        if settings.analysis_scheduler_enabled:
            analysis_scheduler.start_scheduler()
        
        logger.info("✓ Application started successfully")
    
    except LiellaException as e:
        logger.critical(f"Critical startup error: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    try:
        logger.info("Shutting down...")
        if settings.analysis_scheduler_enabled:
            analysis_scheduler.stop_scheduler()
        logger.info("✓ Application shut down cleanly")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(LiellaException)
async def liella_exception_handler(request, exc):
    logger.error(f"Application error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"error": str(exc), "type": type(exc).__name__}
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"DATABASE FAILURE: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Database sync failed.", "type": "DatabaseError"}
    )

@app.exception_handler(Exception)
async def universal_exception_handler(request: Request, exc: Exception):
    logger.error(f"UNHANDLED SYSTEM ERROR: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "An internal error occurred.", "type": "InternalError"}
    )

# Routes
app.include_router(health.router)
app.include_router(submissions.router)
app.include_router(analysis.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )