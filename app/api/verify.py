"""Face verification API: verify 3 images (same person) and optional store."""
import logging
import time
from typing import List, Optional

import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..schemas.response import (
    ImageAnalysis,
    QualityCheck,
    StoredImageInfo,
    SimilarityScores,
    VerificationResponse,
    VerifyAndStoreResponse,
)
from ..services.embedding import EmbeddingExtractor
from ..services.face_detector import FaceDetector
from ..services.quality_check import QualityChecker
from ..services.similarity import SimilarityComputer
from ..services.storage import save_verified_batch
from ..utils.image_utils import ImageProcessor

logger = logging.getLogger(__name__)
router = APIRouter()

face_detector = None
embedding_extractor = None
similarity_computer = None


def get_services():
    global face_detector, embedding_extractor, similarity_computer
    if face_detector is None:
        logger.info("Initializing face detection services...")
        face_detector = FaceDetector()
        embedding_extractor = EmbeddingExtractor()
        similarity_computer = SimilarityComputer()
        logger.info("Services initialized")
    return face_detector, embedding_extractor, similarity_computer


@router.post("/verify", response_model=VerificationResponse)
async def verify_faces(
    image1: UploadFile = File(...),
    image2: UploadFile = File(...),
    image3: UploadFile = File(...),
):
    """Verify that 3 images contain the same person. Does not store images."""
    start_time = time.time()
    try:
        detector, extractor, comparator = get_services()
        images, image_names = [image1, image2, image3], ["image1", "image2", "image3"]
        embeddings, image_analyses = [], []

        for img_file, img_name in zip(images, image_names):
            analysis = ImageAnalysis(image_name=img_name, face_detected=False)
            img_bytes = await img_file.read()
            img_array = ImageProcessor.bytes_to_numpy(img_bytes)
            if img_array is None:
                raise HTTPException(status_code=400, detail=f"{img_name}: Invalid image format")
            img_array = ImageProcessor.resize_image(img_array)

            success, face, message = detector.detect_single_face(img_array)
            if not success:
                raise HTTPException(status_code=400, detail=f"{img_name}: {message}")

            analysis.face_detected = True
            analysis.face_info = detector.get_face_info(face)
            area = face["facial_area"]
            bbox = np.array([area["x"], area["y"], area["x"] + area["w"], area["y"] + area["h"]])

            status, quality_details = QualityChecker.perform_all_checks(
                image=img_array, bbox=bbox, det_score=face["confidence"]
            )
            analysis.quality_checks = {n: QualityCheck(**d) for n, d in quality_details.items()}
            if status == "REJECT":
                failed = [f"{n}: {d['message']}" for n, d in quality_details.items() if not d.get("passed", True)]
                raise HTTPException(status_code=400, detail=f"{img_name}: Quality check failed - {'; '.join(failed)}")

            embedding = extractor.extract_embedding(face)
            if embedding is None or not extractor.validate_embedding(embedding):
                raise HTTPException(status_code=500, detail=f"{img_name}: Failed to extract face embedding")

            embeddings.append(embedding)
            image_analyses.append(analysis)

        similarities = comparator.compute_pairwise_similarities(embeddings)
        result, confidence, analysis_details = comparator.verify_same_person(similarities)
        msg = (
            f"All 3 images contain the SAME person (confidence: {confidence:.2%})"
            if result == "SAME_PERSON"
            else f"Images contain DIFFERENT persons (confidence: {confidence:.2%})"
        )
        logger.info("Verify completed in %.2fs: %s", time.time() - start_time, result)
        return VerificationResponse(
            result=result,
            confidence=confidence,
            similarity=SimilarityScores(**similarities),
            analysis=analysis_details,
            image_analyses=image_analyses,
            message=msg,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Verify error: %s", e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/verify-and-store", response_model=VerifyAndStoreResponse)
@router.post("/verify-and-store", response_model=VerifyAndStoreResponse)
async def verify_and_store_faces(
    image1: UploadFile = File(...),
    image2: UploadFile = File(...),
    image3: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
):
    """
    Verify that all 3 images are the same person. If yes, mark verified and store
    images in DB; return stored image IDs. If not, return 400 and do not store.
    """
    start_time = time.time()
    images = [image1, image2, image3]
    image_names = ["image1", "image2", "image3"]

    try:
        detector, extractor, comparator = get_services()
        embeddings = []
        image_analyses: List[ImageAnalysis] = []
        image_data_list: List[tuple] = []  # (bytes, filename, mimetype)

        for idx, (img_file, img_name) in enumerate(zip(images, image_names), 1):
            analysis = ImageAnalysis(image_name=img_name, face_detected=False)
            img_bytes = await img_file.read()
            img_array = ImageProcessor.bytes_to_numpy(img_bytes)

            if img_array is None:
                analysis.error = "Invalid or corrupted image"
                image_analyses.append(analysis)
                raise HTTPException(
                    status_code=400,
                    detail=f"{img_name}: Invalid image format"
                )

            img_array = ImageProcessor.resize_image(img_array)
            success, face, message = detector.detect_single_face(img_array)
            if not success:
                analysis.error = message
                image_analyses.append(analysis)
                raise HTTPException(status_code=400, detail=f"{img_name}: {message}")

            analysis.face_detected = True
            face_info = detector.get_face_info(face)
            analysis.face_info = face_info
            area = face["facial_area"]
            bbox = np.array([
                area["x"], area["y"],
                area["x"] + area["w"], area["y"] + area["h"]
            ])
            status, quality_details = QualityChecker.perform_all_checks(
                image=img_array, bbox=bbox, det_score=face["confidence"]
            )
            analysis.quality_checks = {
                name: QualityCheck(**details)
                for name, details in quality_details.items()
            }
            if status == "REJECT":
                failed_checks = [
                    f"{name}: {details['message']}"
                    for name, details in quality_details.items()
                    if not details.get("passed", True)
                ]
                analysis.error = "; ".join(failed_checks)
                image_analyses.append(analysis)
                raise HTTPException(
                    status_code=400,
                    detail=f"{img_name}: Quality check failed - {analysis.error}"
                )
            image_analyses.append(analysis)

            embedding = extractor.extract_embedding(face)
            if embedding is None or not extractor.validate_embedding(embedding):
                raise HTTPException(
                    status_code=500,
                    detail=f"{img_name}: Failed to extract face embedding"
                )
            embeddings.append(embedding)
            filename = img_file.filename or f"{img_name}.jpg"
            image_data_list.append((img_bytes, filename, img_file.content_type))

        similarities = comparator.compute_pairwise_similarities(embeddings)
        result, confidence, analysis_details = comparator.verify_same_person(similarities)

        if result != "SAME_PERSON":
            processing_time = time.time() - start_time
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "DIFFERENT_PERSON",
                    "message": f"Images do not appear to be the same person (confidence: {confidence:.2%}). Verification failed.",
                    "confidence": confidence,
                    "processing_time_seconds": round(processing_time, 2),
                }
            )

        # Store all 3 images and create DB records
        records = save_verified_batch(image_data_list, user_id)
        stored = [
            StoredImageInfo(
                id=r.id,
                storage_path=r.storage_path,
                original_filename=r.original_filename,
                mimetype=r.mimetype,
                size_bytes=r.size_bytes,
            )
            for r in records
        ]

        return VerifyAndStoreResponse(
            result=result,
            confidence=confidence,
            similarity=SimilarityScores(**similarities),
            message="All 3 images verified as same person and stored successfully.",
            stored_images=stored,
            image_analyses=image_analyses,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Verify-and-store error: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


# =====================================================
# HEALTH
# =====================================================
@router.get("/health")
async def health_check():
    from ..schemas.response import HealthResponse

    try:
        detector, _, _ = get_services()
        # FaceDetector has no .app; consider loaded if singleton exists
        model_loaded = detector is not None

        return HealthResponse(
            status="healthy" if model_loaded else "initializing",
            model_loaded=model_loaded,
            version="1.0.0"
        )
    except Exception:
        return HealthResponse(
            status="unhealthy",
            model_loaded=False,
            version="1.0.0"
        )
