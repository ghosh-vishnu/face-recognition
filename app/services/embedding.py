import logging

import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)


class EmbeddingExtractor:
    def __init__(self):
        """Initialize embedding extractor."""
        self.embedding_dim = 512

    def extract_embedding(self, face) -> Optional[np.ndarray]:
        try:
            if isinstance(face, dict) and "encoding" in face:
                embedding = face["encoding"]
            else:
                logger.debug("Face object does not have encoding")
                return None

            if not isinstance(embedding, np.ndarray):
                embedding = np.array(embedding)

            if embedding is None or len(embedding) == 0:
                logger.debug("Empty embedding")
                return None

            if embedding.shape[0] != self.embedding_dim:
                self.embedding_dim = embedding.shape[0]

            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

            return embedding.astype(np.float32)

        except Exception as e:
            logger.warning("Error extracting embedding: %s", e)
            return None

    def extract_batch_embeddings(self, faces: list) -> list:
        embeddings = []
        for face in faces:
            emb = self.extract_embedding(face)
            embeddings.append(emb)
        return embeddings
    
    def validate_embedding(self, embedding: np.ndarray) -> bool:
        if embedding is None:
            return False
        
        if not isinstance(embedding, np.ndarray):
            return False
        
        if embedding.shape[0] != self.embedding_dim:
            return False
        
        # Check for NaN or Inf
        if np.any(np.isnan(embedding)) or np.any(np.isinf(embedding)):
            return False
        
        # Check if normalized (L2 norm should be close to 1.0)
        norm = np.linalg.norm(embedding)
        if not (0.99 <= norm <= 1.01):
            return False
        
        return True
