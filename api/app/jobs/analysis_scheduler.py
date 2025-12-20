# app/jobs/analysis_scheduler.py

from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import AnalysisResult, Franchise, Subgroup, SubmissionStatus
from app.services.analysis import AnalysisService

scheduler = BackgroundScheduler()


def recompute_all_analyses():
    """Recompute all analyses for all franchises/subgroups"""
    print(f"[{datetime.utcnow()}] Starting analysis recomputation...")

    db = SessionLocal()
    try:
        franchises = db.query(Franchise).all()

        for franchise in franchises:
            subgroups = db.query(Subgroup).filter_by(franchise_id=franchise.id).all()

            for subgroup in subgroups:
                print(f"  Computing analyses for {franchise.name}/{subgroup.name}...")

                # Compute all analysis types
                divergence = AnalysisService.compute_divergence_matrix(
                    str(franchise.id), str(subgroup.id), db
                )
                controversy = AnalysisService.compute_controversy(
                    str(franchise.id), str(subgroup.id), db
                )

                # Count valid submissions
                submission_count = (
                    db.query(db.func.count(db.models.Submission.id))
                    .filter(
                        db.models.Submission.franchise_id == franchise.id,
                        db.models.Submission.subgroup_id == subgroup.id,
                        db.models.Submission.submission_status
                        == SubmissionStatus.VALID,
                    )
                    .scalar()
                )

                # Store/update results
                for analysis_type, result_data in [
                    ("DIVERGENCE", divergence),
                    ("CONTROVERSY", controversy),
                ]:
                    existing = (
                        db.query(AnalysisResult)
                        .filter(
                            AnalysisResult.franchise_id == franchise.id,
                            AnalysisResult.subgroup_id == subgroup.id,
                            AnalysisResult.analysis_type == analysis_type,
                        )
                        .first()
                    )

                    if existing:
                        existing.result_data = result_data
                        existing.computed_at = datetime.utcnow()
                        existing.based_on_submissions = submission_count
                    else:
                        db.add(
                            AnalysisResult(
                                franchise_id=franchise.id,
                                subgroup_id=subgroup.id,
                                analysis_type=analysis_type,
                                result_data=result_data,
                                computed_at=datetime.utcnow(),
                                based_on_submissions=submission_count,
                            )
                        )

                db.commit()

        print(f"[{datetime.utcnow()}] Analysis recomputation complete!")

    except Exception as e:
        print(f"[ERROR] Analysis recomputation failed: {str(e)}")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler"""
    if scheduler.running:
        return

    trigger = CronTrigger(
        hour=settings.analysis_schedule_hour, minute=settings.analysis_schedule_minute
    )

    scheduler.add_job(
        recompute_all_analyses,
        trigger=trigger,
        id="recompute_analyses",
        name="Recompute All Analyses",
        replace_existing=True,
    )

    scheduler.start()
    print("Analysis scheduler started")


def stop_scheduler():
    """Stop the background scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        print("Analysis scheduler stopped")
