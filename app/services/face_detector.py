import numpy as np
from deepface import DeepFace
from typing import Optional, Tuple, Dict
import cv2
import os


class FaceDetector:
    
    def __init__(self):
        """Initialize DeepFace model"""
        self.model_name = 'Facenet512'  # High accuracy model
        self.detector_backend = 'opencv'  # Fast detector
        print("DeepFace model initialized successfully")
    
    def _initialize_model(self):
        # DeepFace initializes on first use
        pass
    
    def detect_single_face(self, image: np.ndarray) -> Tuple[bool, Optional[Dict], str]:
        try:
            # DeepFace expects RGB images
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect faces using DeepFace
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
        # facial_area is {x, y, w, h}
        area = face['facial_area']
        x, y, w, h = area['x'], area['y'], area['w'], area['h']
        
        info = {
            'bbox': [x, y, x + w, y + h],  # [x1, y1, x2, y2]
            'confidence': float(face.get('confidence', 1.0)),
            'face_area': int(w * h),
            'embedding_shape': face['encoding'].shape if face['encoding'] is not None else None
        }
        
        return info
    
    def visualize_detection(self, image: np.ndarray, face) -> np.ndarray:
        vis_image = image.copy()
        area = face['facial_area']
        x, y, w, h = area['x'], area['y'], area['w'], area['h']
        
        # Draw bounding box
        cv2.rectangle(
            vis_image,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )
        
        # Draw confidence
        conf = face.get('confidence', 1.0)
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
