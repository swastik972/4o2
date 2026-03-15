"""
TrainingRun ORM model — tracks AI model training jobs.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class TrainingRun(Base):
    __tablename__ = "training_runs"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    model_type = Column(String(100), nullable=False)  # e.g. "yolo", "resnet", "sklearn"
    status = Column(
        String(50), nullable=False, default="pending"
    )  # pending | running | completed | failed
    metrics = Column(Text, nullable=True)  # JSON string of training metrics
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    dataset = relationship("Dataset", back_populates="training_runs")

    def __repr__(self) -> str:
        return (
            f"<TrainingRun(id={self.id}, model='{self.model_type}', "
            f"status='{self.status}')>"
        )
