"""
Celery background tasks for long-running AI operations.
"""

import json
import traceback

from loguru import logger

from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.model_service import ModelService
from app.services.training_pipeline import TrainingPipeline
from app.core.config import settings


@celery_app.task(bind=True, name="train_model_task", max_retries=2)
def train_model_task(self, training_run_id: int) -> dict:
    """
    Execute a full model training pipeline as a background task.

    Args:
        training_run_id: ID of the TrainingRun record.

    Returns:
        dict with training metrics.
    """
    db = SessionLocal()
    try:
        service = ModelService(db)

        # Mark as running
        run = service.update_training_status(training_run_id, status="running")
        dataset = run.dataset

        logger.info(
            "Task: training run #{} — model={}, dataset='{}'",
            training_run_id,
            run.model_type,
            dataset.name,
        )

        # Run pipeline
        pipeline = TrainingPipeline(
            dataset_path=dataset.file_path,
            model_type=run.model_type,
        )
        metrics = pipeline.run(output_dir=str(settings.model_path))

        # Mark as completed
        service.update_training_status(
            training_run_id,
            status="completed",
            metrics=metrics,
        )
        logger.info("Task: training run #{} completed ✓", training_run_id)
        return metrics

    except Exception as exc:
        logger.error("Task: training run #{} failed — {}", training_run_id, exc)
        try:
            service.update_training_status(
                training_run_id,
                status="failed",
                error_message=traceback.format_exc(),
            )
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@celery_app.task(name="preprocess_dataset_task")
def preprocess_dataset_task(dataset_path: str) -> dict:
    """
    Preprocess a dataset as a background task (placeholder).

    Args:
        dataset_path: Path to the dataset directory.

    Returns:
        dict with preprocessing summary.
    """
    logger.info("Preprocessing dataset at {}", dataset_path)

    # Placeholder — count files, validate structure
    from app.utils.file_utils import get_directory_info

    info = get_directory_info(dataset_path)
    logger.info("Preprocessing complete: {}", info)
    return {"status": "completed", "info": info}
