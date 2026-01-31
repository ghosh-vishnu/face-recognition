from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    JSON,
    ForeignKey,
    Float,
    Boolean,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="analyst")
    created_at = Column(DateTime, default=datetime.utcnow)
    datasets = relationship("Dataset", back_populates="owner")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    schema = Column(JSON, nullable=True)
    row_count = Column(Integer, nullable=True)
    quality_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner = relationship("User", back_populates="datasets")
    charts = relationship("ChartArtifact", back_populates="dataset")
    insights = relationship("Insight", back_populates="dataset")
    forecasts = relationship("ForecastArtifact", back_populates="dataset")


class ChartArtifact(Base):
    __tablename__ = "charts"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    chart_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    dataset = relationship("Dataset", back_populates="charts")


class Insight(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    role = Column(String, nullable=False)
    headline = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, default="medium")
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    dataset = relationship("Dataset", back_populates="insights")


class ForecastArtifact(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    target_column = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    forecast_summary = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    dataset = relationship("Dataset", back_populates="forecasts")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String, default="info")
    is_acknowledged = Column(Boolean, default=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ActionTrigger(Base):
    __tablename__ = "action_triggers"

    id = Column(Integer, primary_key=True, index=True)
    insight_id = Column(Integer, ForeignKey("insights.id"))
    action_type = Column(String, nullable=False)
    api_url = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


