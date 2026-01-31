import cv2
import numpy as np
from typing import Dict, Tuple, Literal


class QualityChecker:
    # ================= THRESHOLDS =================
    MIN_BLUR_SCORE = 18.0
    MIN_BRIGHTNESS = 30
    MAX_BRIGHTNESS = 225
    MIN_FACE_SIZE = 80
    MIN_FACE_SCORE = 0.7

    # ================= METRIC CALCULATIONS =================

    @staticmethod
    def calculate_blur(image: np.ndarray) -> float:
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            return float(cv2.Laplacian(gray, cv2.CV_64F).var())
        except Exception:
            # never crash on blur
            return 0.0

    @staticmethod
    def calculate_brightness(image: np.ndarray) -> float:
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            return float(np.mean(gray))
        except Exception:
            return 0.0

    # ================= CHECKS =================

    @staticmethod
    def check_blur(blur_score: float) -> Tuple[bool, str]:
        if blur_score < QualityChecker.MIN_BLUR_SCORE:
            return False, f"Image slightly blurry (score: {blur_score:.1f})"
        return True, "Blur OK"

    @staticmethod
    def check_brightness(brightness: float) -> Tuple[bool, str]:
        if brightness < QualityChecker.MIN_BRIGHTNESS:
            return False, f"Image too dark ({brightness:.1f})"
        if brightness > QualityChecker.MAX_BRIGHTNESS:
            return False, f"Image too bright ({brightness:.1f})"
        return True, "Brightness OK"

    @staticmethod
    def check_face_quality(
        bbox: np.ndarray,
        det_score: float,
        image_shape: Tuple[int, int]
    ) -> Tuple[bool, str, np.ndarray]:

        if det_score < QualityChecker.MIN_FACE_SCORE:
            return False, f"Low face confidence ({det_score:.2f})", bbox

        # ---- sanitize bbox ----
        h, w = image_shape
        bbox = np.array(bbox, dtype=np.int32)

        x1 = max(0, min(bbox[0], w - 1))
        y1 = max(0, min(bbox[1], h - 1))
        x2 = max(0, min(bbox[2], w))
        y2 = max(0, min(bbox[3], h))

        width = x2 - x1
        height = y2 - y1

        if width < QualityChecker.MIN_FACE_SIZE or height < QualityChecker.MIN_FACE_SIZE:
            return False, f"Face too small ({width}x{height}px)", np.array([x1, y1, x2, y2])

        return True, "Face OK", np.array([x1, y1, x2, y2])

    # ================= FINAL PIPELINE =================

    @staticmethod
    def perform_all_checks(
        image: np.ndarray,
        bbox: np.ndarray,
        det_score: float
    ) -> Tuple[Literal["ACCEPT", "WARN", "REJECT"], Dict[str, Dict]]:

        report: Dict[str, Dict] = {}
        warnings = []

        # ---- Image safety ----
        if image is None or image.size == 0:
            return "REJECT", {"reason": "Invalid image"}

        # ---- Calculate metrics ----
        blur_score = QualityChecker.calculate_blur(image)
        brightness = QualityChecker.calculate_brightness(image)

        # ---- FACE CHECK (HARD REJECT) ----
        face_ok, face_msg, safe_bbox = QualityChecker.check_face_quality(
            bbox, det_score, image.shape[:2]
        )

        report["face"] = {
            "passed": face_ok,
            "message": face_msg,
            "confidence": round(det_score, 3),
            "bbox": safe_bbox.tolist()
        }

        if not face_ok:
            return "REJECT", report

        # ---- BLUR CHECK (SOFT) ----
        blur_ok, blur_msg = QualityChecker.check_blur(blur_score)
        report["blur"] = {
            "passed": blur_ok,
            "message": blur_msg,
            "score": round(blur_score, 2)
        }
        if not blur_ok:
            warnings.append("blur")

        # ---- BRIGHTNESS CHECK (SOFT) ----
        bright_ok, bright_msg = QualityChecker.check_brightness(brightness)
        report["brightness"] = {
            "passed": bright_ok,
            "message": bright_msg,
            "value": round(brightness, 2)
        }
        if not bright_ok:
            warnings.append("brightness")

        # ---- FINAL DECISION ----
        if warnings:
            report["warnings"] = warnings
            return "WARN", report

        return "ACCEPT", report
