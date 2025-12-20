# app/main.py

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
        
        # Initialize database connection
        database.init_engine()
        database.init_db()
        
        # Seed if empty
        db = database.get_session()
        try:
            from app.models import Song
            song_count = db.query(Song).count()
            if song_count == 0:
                logger.info("Database empty, running seeds...")
                DatabaseSeeder.seed_all(db)
            else:
                logger.info(f"Database has {song_count} songs")
        except Exception as e:
            logger.error(f"Seeding error: {str(e)}")
            db.close()
            raise
        finally:
            db.close()
        
        # Start scheduler
        if settings.analysis_scheduler_enabled:
            analysis_scheduler.start_scheduler()
        
        logger.info("✓ Application started successfully")
    
    except LiellaException as e:
        logger.critical(f"Critical startup error: {str(e)}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected startup error: {str(e)}")
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