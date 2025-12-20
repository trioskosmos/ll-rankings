# app/jobs/analysis_scheduler.py

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import AnalysisResult, Franchise, Subgroup, Submission, SubmissionStatus
from app.services.analysis import AnalysisService

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def recompute_all_analyses():
    """Recompute all statistical metrics for the entire franchise."""
    logger.info("Starting background analysis recomputation...")
    db = SessionLocal()

    try:
        franchises = db.query(Franchise).all()

        for franchise in franchises:
            f_id_str = str(franchise.id)
            subgroups = db.query(Subgroup).filter_by(franchise_id=franchise.id).all()

            # 1. SUBGROUP-LEVEL ANALYSIS
            # Metrics that look at songs within a specific group (e.g. CatChu!)
            for subgroup in subgroups:
                s_id_str = str(subgroup.id)
                logger.info(f"Computing subgroup metrics: {franchise.name}/{subgroup.name}")

                # Compute results
                divergence = AnalysisService.compute_divergence_matrix(
                    f_id_str, s_id_str, db
                )
                controversy = AnalysisService.compute_controversy(
                    f_id_str, s_id_str, db
                )
                takes = AnalysisService.compute_hot_takes(
                    f_id_str, s_id_str, db
                )

                valid_subs = db.query(Submission).filter(
                    Submission.subgroup_id == subgroup.id,
                    Submission.submission_status == SubmissionStatus.VALID
                ).count()

                # Store subgroup results
                analysis_map = {
                    "DIVERGENCE": divergence,
                    "CONTROVERSY": controversy,
                    "TAKES": takes
                }

                for a_type, data in analysis_map.items():
                    update_analysis_record(
                        db, franchise.id, subgroup.id, a_type, data, valid_subs
                    )

            # 2. FRANCHISE-LEVEL ANALYSIS
            # Metrics that aggregate data across all subgroups (e.g. Spice Meter)
            logger.info(f"Computing franchise metrics for {franchise.name}")
            
            spice_data = AnalysisService.compute_spice_meter(f_id_str, db)
            
            total_subs = db.query(Submission).filter(
                Submission.franchise_id == franchise.id,
                Submission.submission_status == SubmissionStatus.VALID
            ).count()

            update_analysis_record(
                db, franchise.id, None, "SPICE", spice_data, total_subs
            )

            db.commit()

        logger.info("Analysis recomputation complete.")

    except Exception as e:
        logger.error(f"Analysis job failed: {str(e)}")
        db.rollback()
    finally:
        db.close()


def update_analysis_record(db, f_id, s_id, a_type, data, sub_count):
    """Upsert helper for the AnalysisResult table."""
    existing = db.query(AnalysisResult).filter(
        AnalysisResult.franchise_id == f_id,
        AnalysisResult.subgroup_id == s_id,
        AnalysisResult.analysis_type == a_type
    ).first()

    if existing:
        existing.result_data = data
        existing.computed_at = datetime.utcnow()
        existing.based_on_submissions = sub_count
    else:
        new_result = AnalysisResult(
            franchise_id=f_id,
            subgroup_id=s_id,
            analysis_type=a_type,
            result_data=data,
            computed_at=datetime.utcnow(),
            based_on_submissions=sub_count
        )
        db.add(new_result)


def start_scheduler():
    """Register and start the cron job."""
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
    """Shut down the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Analysis scheduler stopped.")