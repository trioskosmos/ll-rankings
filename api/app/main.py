
# app/main.py
# Trigger reload: Oshi Detector consolidated and cleaned (Reload Triggered)

from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app import database  # Import module, not individual exports
from app.models import Song, Franchise
from app.seeds.init import DatabaseSeeder
from app.exceptions import LiellaException
from app.logging_config import setup_logging
from app.api.v1 import submissions, analysis, health, users
from app.jobs import analysis_scheduler

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

from app.seeds.import_rankings import import_user_rankings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        logger.info("Starting application...")
        database.init_engine()
        database.init_db()
        
        # DEBUG: Check volume mounts
        import os
        try:
            logger.info(f"DEBUG: Content of /project_root: {os.listdir('/project_root')}")
            if os.path.exists('/project_root/data'):
                logger.info(f"DEBUG: Content of /project_root/data: {os.listdir('/project_root/data')}")
            else:
                logger.error("DEBUG: /project_root/data DOES NOT EXIST")
        except Exception as e:
            logger.error(f"DEBUG: Failed to list directories: {e}")
        
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
                # Seed songs from {franchise}_songs.json
                # We run this every time to ensure new songs are added.
                # seed_songs checks for existence internally.
                try:
                    # logger.info(f"Syncing songs for {franchise_name}...")
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
            
            # Import user rankings from CSV (only if enabled via config)
            if settings.seed_rankings_on_startup:
                try:
                    logger.info("Syncing user rankings from CSV...")
                    imported = import_user_rankings(db)
                    logger.info(f"✓ Imported/updated {imported} user rankings")
                except Exception as e:
                    logger.warning(f"Could not import user rankings: {str(e)}")
            else:
                logger.info("Skipping user rankings csv import (SEED_RANKINGS_ON_STARTUP=False)")
            
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

@app.middleware("http")
async def add_pna_header(request: Request, call_next):
    if request.method == "OPTIONS":
        response = await call_next(request)
        response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response
    
    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

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
app.include_router(users.router)


# Static files & Data directory
# Logic: explicitly check if /project_root exists (Docker volume), otherwise use relative path (Local)
DOCKER_ROOT = Path("/project_root")
LOCAL_ROOT = Path(__file__).resolve().parent.parent.parent

if DOCKER_ROOT.exists():
    FRONTEND_DIR = DOCKER_ROOT
    DATA_DIR = DOCKER_ROOT / "data"
else:
    FRONTEND_DIR = LOCAL_ROOT
    DATA_DIR = LOCAL_ROOT / "data"

# Mount /data to serve song-info.json and other data files
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")

# Serve static JS/CSS files
@app.get("/app.js")
async def serve_app_js():
    return FileResponse(FRONTEND_DIR / "app.js", media_type="application/javascript")

@app.get("/dash_utils.js")
async def serve_dash_utils_js():
    return FileResponse(FRONTEND_DIR / "dash_utils.js", media_type="application/javascript")

@app.get("/users.html")
async def serve_users_html():
    return FileResponse(FRONTEND_DIR / "users.html", media_type="text/html")

# Root route - serve index.html
@app.get("/")
async def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html", media_type="text/html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )