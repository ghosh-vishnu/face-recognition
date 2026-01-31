import logging

import cv2
import numpy as np
from deepface import DeepFace
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class FaceDetector:
    def __init__(self):
        """Initialize DeepFace model."""
        self.model_name = "Facenet512"
        self.detector_backend = "opencv"
        logger.info("DeepFace model initialized successfully")

    def _initialize_model(self):
        pass

    def detect_single_face(self, image: np.ndarray) -> Tuple[bool, Optional[Dict], str]:
        try:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            try:
                face_objs = DeepFace.extract_faces(
                    img_path=rgb_image,
                    detector_backend=self.detector_backend,
                    enforce_detection=True
                )
            except ValueError as e:
                if "Face could not be detected" in str(e):
                    return False, None, "No face detected in image"
                raise e
            
            # Validate exactly one face
            if len(face_objs) == 0:
                return False, None, "No face detected in image"
            
            if len(face_objs) > 1:
                return False, None, f"Multiple faces detected ({len(face_objs)}). Please upload image with single face"
            
            # Extract embedding using DeepFace
            embedding_obj = DeepFace.represent(
                img_path=rgb_image,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                enforce_detection=True
            )
            
            face_obj = face_objs[0]
            
            # Create face data object
            face_data = {
                'facial_area': face_obj['facial_area'],  # {x, y, w, h}
                'confidence': face_obj.get('confidence', 1.0),
                'encoding': np.array(embedding_obj[0]['embedding']),
                'image': rgb_image
            }
            
            return True, face_data, "Face detected successfully"

        except Exception as e:
            return False, None, f"Face detection error: {str(e)}"

    def get_face_info(self, face) -> Dict:
        area = face["facial_area"]
        x, y, w, h = area['x'], area['y'], area['w'], area['h']
        
        info = {
            "bbox": [x, y, x + w, y + h],
            "confidence": float(face.get("confidence", 1.0)),
            "face_area": int(w * h),
            "embedding_shape": face["encoding"].shape if face["encoding"] is not None else None,
        }
        return info

    def visualize_detection(self, image: np.ndarray, face) -> np.ndarray:
        vis_image = image.copy()
        area = face["facial_area"]
        x, y, w, h = area["x"], area["y"], area["w"], area["h"]
        cv2.rectangle(
            vis_image,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )
        conf = face.get("confidence", 1.0)
        cv2.putText(
            vis_image,
            f"Face: {conf:.2f}",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2
        )
        
        return vis_image
