"""
Minimal DB models for the face-verification microservice.

This service only stores images after they have been verified.
Keep schema minimal to match the dating-app verification flow.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean

from .database import Base


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    # Optional: id/reference from the main (nodejs) auth/user service
    user_id = Column(String, nullable=True, index=True)
    original_filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    mimetype = Column(String, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def mark_verified(self):
        self.verified = True
        self.verified_at = datetime.utcnow()