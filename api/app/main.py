# app/main.py

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app import database  # Import module, not individual exports
from app.models import Song, Franchise
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
            
            # 1. Ensure all standard franchises exist in the DB
            DatabaseSeeder.seed_franchises(db)
            
            # 2. Define the active pool to seed/sync
            franchises = ["liella", "aqours", "u's", "nijigasaki", "hasunosora"]
            
            for franchise_name in franchises:
                logger.info(f"Processing startup sync for: {franchise_name}")
                
                # Fetch franchise object to check song population
                f_obj = db.query(Franchise).filter_by(name=franchise_name).first()
                if not f_obj:
                    continue
                
                # Seed songs from {franchise}_songs.json only if that franchise has no songs
                song_count = db.query(Song).filter_by(franchise_id=f_obj.id).count()
                if song_count == 0:
                    try:
                        logger.info(f"Song table for {franchise_name} empty, loading JSON...")
                        DatabaseSeeder.seed_songs(db, franchise_name)
                    except Exception as e:
                        logger.warning(f"Could not seed songs for {franchise_name}: {str(e)}")

                # SUBGROUP SYNCHRONIZATION
                # This runs every boot to allow for TOML updates. 
                # If no subgroups are defined in the TOML for this franchise, the seeder will skip.
                try:
                    DatabaseSeeder.seed_subgroups(db, franchise_name)
                except Exception as e:
                    logger.info(f"Skipping subgroup sync for {franchise_name}: No definitions found in TOML.")

            total_songs = db.query(Song).count()
            logger.info(f"Ready: {total_songs} total songs in system.")
            
        except Exception as e:
            logger.error(f"Global seeding error: {str(e)}")
            db.close()
            raise
        finally:
            db.close()
        
        # Start background analysis engine
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