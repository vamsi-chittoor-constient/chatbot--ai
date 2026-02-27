"""
Local Embedding Service using Sentence Transformers
=====================================================
Provides TRUE semantic search without requiring OpenAI API access.

Uses sentence-transformers with lightweight models that run locally.
No API costs, works offline, and provides real semantic understanding.
"""

from typing import List
import structlog
from sentence_transformers import SentenceTransformer
import numpy as np

logger = structlog.get_logger("ai_services.local_embedding")


class LocalEmbeddingService:
    """
    Local embedding service using Sentence Transformers.

    Uses 'all-MiniLM-L6-v2' model:
    - Fast and lightweight (22MB model)
    - Good quality embeddings (384 dimensions)
    - No API costs or rate limits
    - Works offline
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize local embedding service.

        Args:
            model_name: Sentence transformer model to use
                       Default: all-MiniLM-L6-v2 (fast, lightweight)
                       Alternative: all-mpnet-base-v2 (better quality, slower)
        """
        logger.info(
            "Loading local embedding model",
            model_name=model_name
        )

        # Load model (downloads on first use, then cached)
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

        logger.info(
            "Local embedding service initialized",
            model=model_name,
            dimension=self.dimension
        )

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for given text.

        Args:
            text: Text to generate embedding for

        Returns:
            List of floats representing the embedding vector
        """
        try:
            # Clean up text
            text = " ".join(text.split())

            # Truncate to avoid memory issues
            if len(text) > 8000:
                text = text[:8000]
                logger.warning("Text truncated to 8000 characters")

            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)

            # Convert numpy array to list
            embedding_list = embedding.tolist()

            logger.debug(
                "Generated embedding",
                text_length=len(text),
                embedding_dimension=len(embedding_list)
            )

            return embedding_list

        except Exception as e:
            logger.error(
                "Failed to generate embedding",
                error=str(e),
                exc_info=True
            )
            raise

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing is faster).

        Args:
            texts: List of texts to generate embeddings for

        Returns:
            List of embedding vectors
        """
        try:
            # Clean up texts
            cleaned_texts = [" ".join(text.split()) for text in texts]

            # Batch encode (much faster than one-by-one)
            embeddings = self.model.encode(
                cleaned_texts,
                convert_to_numpy=True,
                show_progress_bar=len(cleaned_texts) > 10  # Show progress for large batches
            )

            # Convert to list of lists
            embeddings_list = embeddings.tolist()

            logger.info(
                "Batch generated embeddings",
                count=len(texts),
                embedding_dimension=self.dimension
            )

            return embeddings_list

        except Exception as e:
            logger.error(
                "Failed to batch generate embeddings",
                error=str(e),
                exc_info=True
            )
            raise

    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0-1, where 1 is identical)
        """
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Compute cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Clamp to [0, 1] range
        return max(0.0, min(1.0, float(similarity)))


# Global singleton instance
_local_embedding_service = None


def get_local_embedding_service() -> LocalEmbeddingService:
    """Get the global LocalEmbeddingService instance (singleton pattern)."""
    global _local_embedding_service
    if _local_embedding_service is None:
        _local_embedding_service = LocalEmbeddingService()
    return _local_embedding_service


__all__ = ["LocalEmbeddingService", "get_local_embedding_service"]
