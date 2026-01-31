import numpy as np
from typing import Optional
class EmbeddingExtractor:    
    def __init__(self):
        """Initialize embedding extractor"""
        self.embedding_dim = 512
    
    def extract_embedding(self, face) -> Optional[np.ndarray]:
        try:
            # For DeepFace, face is a dict with 'encoding' key
            if isinstance(face, dict) and 'encoding' in face:
                embedding = face['encoding']
            else:
                print("Face object does not have encoding")
                return None
            
            # Ensure it's a numpy array
            if not isinstance(embedding, np.ndarray):
                embedding = np.array(embedding)
            
            # Validate embedding
            if embedding is None or len(embedding) == 0:
                print("Empty embedding")
                return None
            
            # DeepFace Facenet512 uses 512-dim embeddings
            # Update expected dimension dynamically
            if embedding.shape[0] != self.embedding_dim:
                self.embedding_dim = embedding.shape[0]
            
            # Normalize embedding (L2 norm)
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding.astype(np.float32)
            
        except Exception as e:
            print(f"Error extracting embedding: {e}")
            return None
    
    def extract_batch_embeddings(self, faces: list) -> list:
        embeddings = []
        for i, face in enumerate(faces):
            emb = self.extract_embedding(face)
            if emb is not None:
                embeddings.append(emb)
                print(f"Extracted embedding {i+1}/{len(faces)}")
            else:
                embeddings.append(None)
                print(f"Failed to extract embedding {i+1}/{len(faces)}")
        
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
