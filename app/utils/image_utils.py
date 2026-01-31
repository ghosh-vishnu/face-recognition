import io
import logging
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Handle image preprocessing and validation"""
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_FORMATS = ['JPEG', 'JPG', 'PNG']
    
    @staticmethod
    def bytes_to_numpy(image_bytes: bytes) -> Optional[np.ndarray]:
        """
        Convert image bytes to numpy array (BGR format for OpenCV)
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            numpy array in BGR format or None if invalid
        """
        try:
            # Validate size
            if len(image_bytes) > ImageProcessor.MAX_FILE_SIZE:
                raise ValueError(f"Image size exceeds {ImageProcessor.MAX_FILE_SIZE / (1024*1024)}MB")
            
            # Open with PIL for format validation
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            # Validate format
            if pil_image.format not in ImageProcessor.ALLOWED_FORMATS:
                raise ValueError(f"Format {pil_image.format} not allowed. Use: {ImageProcessor.ALLOWED_FORMATS}")
            
            # Convert to RGB then to numpy
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Convert to numpy array (RGB)
            img_array = np.array(pil_image)
            
            # Convert RGB to BGR for OpenCV
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            return img_bgr
            
        except Exception as e:
            logger.warning("Error processing image: %s", e)
            return None
    
    @staticmethod
    def resize_image(image: np.ndarray, max_dimension: int = 1920) -> np.ndarray:
        """
        Resize image if it exceeds max dimension while maintaining aspect ratio
        
        Args:
            image: Input image as numpy array
            max_dimension: Maximum width or height
            
        Returns:
            Resized image
        """
        height, width = image.shape[:2]
        
        if max(height, width) <= max_dimension:
            return image
        
        if height > width:
            new_height = max_dimension
            new_width = int(width * (max_dimension / height))
        else:
            new_width = max_dimension
            new_height = int(height * (max_dimension / width))
        
        resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        return resized
    
    @staticmethod
    def compute_blur_score(image: np.ndarray) -> float:
        """
        Compute blur score using Laplacian variance
        Higher values = sharper image
        
        Args:
            image: Input image
            
        Returns:
            Blur score (variance of Laplacian)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return float(laplacian_var)
    
    @staticmethod
    def compute_brightness(image: np.ndarray) -> float:
        """
        Compute average brightness of image
        
        Args:
            image: Input image
            
        Returns:
            Average brightness (0-255)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gray))
