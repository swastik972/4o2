"""
Celery background tasks for AI model training — Phase 2.
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
def train_model_task(
    self,
    training_run_id: int,
    epochs: int = 10,
    learning_rate: float = 1e-3,
    batch_size: int = 16,
) -> dict:
    """
    Execute a full model training pipeline as a background task.

    Args:
        training_run_id: ID of the TrainingRun record.
        epochs: Number of training epochs.
        learning_rate: Learning rate for optimizer.
        batch_size: Batch size for DataLoaders.

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
            "Task: training run #{} — model={}, dataset='{}', epochs={}",
            training_run_id,
            run.model_type,
            dataset.name,
            epochs,
        )

        # Run full pipeline
        pipeline = TrainingPipeline(
            dataset_path=dataset.file_path,
            model_type=run.model_type,
            epochs=epochs,
            learning_rate=learning_rate,
            batch_size=batch_size,
        )
        metrics = pipeline.run(output_dir=str(settings.model_path))

        # Sanitize metrics for JSON serialization
        serializable_metrics = {
            k: v for k, v in metrics.items()
            if isinstance(v, (int, float, str, list, dict, bool, type(None)))
        }

        # Mark as completed
        service.update_training_status(
            training_run_id,
            status="completed",
            metrics=serializable_metrics,
        )
        logger.info("Task: training run #{} completed ✓", training_run_id)
        return serializable_metrics

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
    Preprocess a dataset as a background task.

    Args:
        dataset_path: Path to the dataset directory.

    Returns:
        dict with preprocessing summary.
    """
    logger.info("Preprocessing dataset at {}", dataset_path)

    from app.services.data_preprocessing import ImagePreprocessor

    try:
        preprocessor = ImagePreprocessor(data_dir=dataset_path)
        preprocessor.load_images()
        X_train, X_val, X_test, y_train, y_val, y_test = preprocessor.split_data()

        result = {
            "status": "completed",
            "total_images": len(preprocessor.image_paths),
            "train_size": len(X_train),
            "val_size": len(X_val),
            "test_size": len(X_test),
            "class_distribution": {
                "pothole": sum(1 for l in preprocessor.labels if l == 1),
                "normal": sum(1 for l in preprocessor.labels if l == 0),
            },
        }
        logger.info("Preprocessing complete: {}", result)
        return result

    except Exception as exc:
        logger.error("Preprocessing failed: {}", exc)
        return {"status": "failed", "error": str(exc)}
