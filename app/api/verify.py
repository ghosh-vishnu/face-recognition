from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import time
import numpy as np

from ..services.face_detector import FaceDetector
from ..services.embedding import EmbeddingExtractor
from ..services.similarity import SimilarityComputer
from ..services.quality_check import QualityChecker
from ..utils.image_utils import ImageProcessor
from ..schemas.response import (
    VerificationResponse,
    SimilarityScores,
    ImageAnalysis,
    QualityCheck
)

router = APIRouter()

# =====================================================
# SINGLETON SERVICES
# =====================================================
face_detector = None
embedding_extractor = None
similarity_computer = None


def get_services():
    global face_detector, embedding_extractor, similarity_computer

    if face_detector is None:
        print("Initializing face detection services...")
        face_detector = FaceDetector()
        embedding_extractor = EmbeddingExtractor()
        similarity_computer = SimilarityComputer()
        print("✓ Services initialized")

    return face_detector, embedding_extractor, similarity_computer


# =====================================================
# VERIFY ENDPOINT
# =====================================================
@router.post("/verify", response_model=VerificationResponse)
async def verify_faces(
    image1: UploadFile = File(...),
    image2: UploadFile = File(...),
    image3: UploadFile = File(...)
):
    start_time = time.time()

    try:
        detector, extractor, comparator = get_services()

        images = [image1, image2, image3]
        image_names = ["image1", "image2", "image3"]

        embeddings = []
        image_analyses: List[ImageAnalysis] = []

        # -------------------------------------------------
        # PROCESS EACH IMAGE
        # -------------------------------------------------
        for idx, (img_file, img_name) in enumerate(zip(images, image_names), 1):
            print(f"\n{'=' * 50}")
            print(f"Processing {img_name} ({idx}/3)")
            print(f"{'=' * 50}")

            analysis = ImageAnalysis(
                image_name=img_name,
                face_detected=False
            )

            # ---------- Read image ----------
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
            print(f"Image shape: {img_array.shape}")

            # ---------- Detect face ----------
            success, face, message = detector.detect_single_face(img_array)
            if not success:
                analysis.error = message
                image_analyses.append(analysis)
                raise HTTPException(
                    status_code=400,
                    detail=f"{img_name}: {message}"
                )

            analysis.face_detected = True
            face_info = detector.get_face_info(face)
            analysis.face_info = face_info
            print(f"Face detected: confidence={face_info['confidence']:.2f}")

            # ---------- bbox ----------
            area = face["facial_area"]
            bbox = np.array([
                area["x"],
                area["y"],
                area["x"] + area["w"],
                area["y"] + area["h"]
            ])

            # =================================================
            # QUALITY CHECK (UPDATED CALL ✅)
            # =================================================
            status, quality_details = QualityChecker.perform_all_checks(
                image=img_array,
                bbox=bbox,
                det_score=face["confidence"]
            )

            # Convert to schema objects
            analysis.quality_checks = {
                name: QualityCheck(**details)
                for name, details in quality_details.items()
            }

            # ---------- HARD REJECT ONLY ----------
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

            # WARN / ACCEPT → continue
            image_analyses.append(analysis)

            # ---------- Embedding ----------
            embedding = extractor.extract_embedding(face)
            if embedding is None or not extractor.validate_embedding(embedding):
                analysis.error = "Failed to extract valid face embedding"
                raise HTTPException(
                    status_code=500,
                    detail=f"{img_name}: Failed to extract face embedding"
                )

            embeddings.append(embedding)
            print(f"Embedding extracted: shape={embedding.shape}")

        # -------------------------------------------------
        # SIMILARITY
        # -------------------------------------------------
        similarities = comparator.compute_pairwise_similarities(embeddings)
        print("Similarities:", similarities)

        result, confidence, analysis_details = comparator.verify_same_person(similarities)

        processing_time = time.time() - start_time
        print(f"Total processing time: {processing_time:.2f}s")

        message = (
            f"All 3 images contain the SAME person (confidence: {confidence:.2%})"
            if result == "SAME_PERSON"
            else f"Images contain DIFFERENT persons (confidence: {confidence:.2%})"
        )

        return VerificationResponse(
            result=result,
            confidence=confidence,
            similarity=SimilarityScores(**similarities),
            analysis=analysis_details,
            image_analyses=image_analyses,
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
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
        model_loaded = detector is not None and detector.app is not None

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
