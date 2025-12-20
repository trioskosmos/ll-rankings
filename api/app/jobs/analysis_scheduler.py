# app/jobs/analysis_scheduler.py

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app import database
from app.models import AnalysisResult, Franchise, Subgroup, Submission, SubmissionStatus
from app.services.analysis import AnalysisService

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

def update_analysis_record(db: Session, franchise_id, subgroup_id, analysis_type, data, sub_count):
    """Safely updates or creates an analysis result record (Upsert logic)."""
    existing = db.query(AnalysisResult).filter(
        AnalysisResult.franchise_id == franchise_id,
        AnalysisResult.subgroup_id == subgroup_id,
        AnalysisResult.analysis_type == analysis_type
    ).first()

    if existing:
        existing.result_data = data
        existing.computed_at = datetime.utcnow()
        existing.based_on_submissions = sub_count
    else:
        new_result = AnalysisResult(
            franchise_id=franchise_id,
            subgroup_id=subgroup_id,
            analysis_type=analysis_type,
            result_data=data,
            computed_at=datetime.utcnow(),
            based_on_submissions=sub_count
        )
        db.add(new_result)

def recompute_all_analyses():
    """Iterates through data and recomputes all metrics."""
    logger.info("Starting background analysis recomputation job...")

    try:
        db = database.get_session()
    except Exception as e:
        logger.error(f"Failed to get database session: {str(e)}")
        return

    try:
        franchises = db.query(Franchise).all()
        if not franchises:
            return

        for franchise in franchises:
            f_id_str = str(franchise.id)
            logger.info(f"--- Processing Franchise: {franchise.name} ---")

            try:
                # Get the count of all valid submissions in this franchise
                franchise_valid_count = db.query(Submission).filter(
                    Submission.franchise_id == franchise.id,
                    Submission.submission_status == SubmissionStatus.VALID
                ).count()

                if franchise_valid_count < 2:
                    logger.info(f"Skipping {franchise.name}: insufficient franchise data.")
                    continue

                subgroups = db.query(Subgroup).filter_by(franchise_id=franchise.id).all()

                for subgroup in subgroups:
                    s_id_str = str(subgroup.id)
                    
                    subgroup_tasks = {
                        "DIVERGENCE": AnalysisService.compute_divergence_matrix,
                        "CONTROVERSY": AnalysisService.compute_controversy,
                        "TAKES": AnalysisService.compute_hot_takes,
                        "COMMUNITY_RANK": AnalysisService.compute_community_rankings
                    }

                    for a_type, calc_func in subgroup_tasks.items():
                        try:
                            data = calc_func(f_id_str, s_id_str, db)
                            # Only save if the task returned data (relativizer found matches)
                            if data:
                                update_analysis_record(db, franchise.id, subgroup.id, a_type, data, franchise_valid_count)
                        except Exception as e:
                            logger.error(f"Error calculating {a_type} for {subgroup.name}: {str(e)}")

                # Franchise-wide Spice Index
                try:
                    spice_data = AnalysisService.compute_spice_meter(f_id_str, db)
                    update_analysis_record(db, franchise.id, None, "SPICE", spice_data, franchise_valid_count)
                except Exception as e:
                    logger.error(f"Error calculating SPICE for {franchise.name}: {str(e)}")

                db.commit()
                logger.info(f"Finished recomputation for {franchise.name}")

            except Exception as e:
                db.rollback()
                logger.error(f"Critical error in franchise {franchise.name} loop: {str(e)}")

    except Exception as e:
        logger.critical(f"Scheduler job failed: {str(e)}")
    finally:
        db.close()

def start_scheduler():
    if not scheduler.running:
        trigger = CronTrigger(
            hour=settings.analysis_schedule_hour,
            minute=settings.analysis_schedule_minute
        )
        scheduler.add_job(
            recompute_all_analyses,
            trigger=trigger,
            id="recompute_all",
            replace_existing=True
        )
        scheduler.start()
        logger.info("Analysis scheduler active.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Analysis scheduler stopped.")
        