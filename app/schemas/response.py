from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class SimilarityScores(BaseModel):
    """Pairwise similarity scores between images"""
    img1_img2: float = Field(..., ge=0.0, le=1.0, description="Similarity between image 1 and 2")
    img1_img3: float = Field(..., ge=0.0, le=1.0, description="Similarity between image 1 and 3")
    img2_img3: float = Field(..., ge=0.0, le=1.0, description="Similarity between image 2 and 3")


class QualityCheck(BaseModel):
    """Quality check result for a single aspect"""
    passed: bool
    message: str
    score: Optional[float] = None
    value: Optional[float] = None
    confidence: Optional[float] = None


class ImageAnalysis(BaseModel):
    """Analysis details for a single image"""
    image_name: str
    face_detected: bool
    quality_checks: Optional[Dict[str, QualityCheck]] = None
    face_info: Optional[Dict] = None
    error: Optional[str] = None


class VerificationResponse(BaseModel):
    """Main verification response"""
    result: str = Field(..., description="SAME_PERSON or DIFFERENT_PERSON")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    similarity: SimilarityScores
    analysis: Optional[Dict] = Field(None, description="Detailed similarity analysis")
    image_analyses: Optional[List[ImageAnalysis]] = Field(None, description="Per-image analysis")
    message: str = Field(..., description="Human-readable result message")


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    details: Optional[str] = None
    code: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model_loaded: bool
    version: str


class StoredImageInfo(BaseModel):
    """Info for one stored image after verification"""
    id: int
    storage_path: str
    original_filename: str
    mimetype: Optional[str] = None
    size_bytes: Optional[int] = None


class VerifyAndStoreResponse(BaseModel):
    """Response when verification passes and images are stored"""
    result: str = Field(..., description="SAME_PERSON")
    confidence: float = Field(..., ge=0.0, le=1.0)
    similarity: SimilarityScores
    message: str
    stored_images: List[StoredImageInfo] = Field(..., description="Saved image records")
    image_analyses: Optional[List[ImageAnalysis]] = None
