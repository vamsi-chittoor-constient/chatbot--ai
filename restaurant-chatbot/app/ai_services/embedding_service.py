"""
Embedding Service
==================
Centralized service for generating embeddings using OpenAI's text-embedding API.
Used for semantic search, recommendations, and similarity matching.
"""

from typing import List
import structlog
import openai
from app.core.config import config

logger = structlog.get_logger("ai_services.embedding_service")


class EmbeddingService:
    """
    Service for generating text embeddings using OpenAI API.

    Provides a centralized, reusable way to generate embeddings
    for search queries, menu items, and other text content.
    """

    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        # Use newer text-embedding-3-small model (cheaper, faster, more accessible)
        self.model = config.OPENAI_MODEL_EMBEDDINGS or "text-embedding-3-small"
        self.dimension = 1536  # text-embedding-3-small produces 1536-dimensional vectors by default

        logger.info(
            "Embedding service initialized",
            model=self.model,
            dimension=self.dimension
        )

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for given text using OpenAI API.

        Args:
            text: Text to generate embedding for

        Returns:
            List of floats representing the embedding vector (1536 dimensions)

        Raises:
            Exception: If embedding generation fails
        """
        try:
            # Clean up text - remove excessive whitespace and newlines
            text = " ".join(text.split())

            # Truncate to avoid token limits (max ~8000 tokens, but we'll be conservative)
            if len(text) > 8000:
                text = text[:8000]
                logger.warning("Text truncated to 8000 characters for embedding")

            # Call OpenAI embeddings API
            response = await self.client.embeddings.create(
                input=text,
                model=self.model
            )

            embedding = response.data[0].embedding

            logger.debug(
                "Generated embedding",
                text_length=len(text),
                embedding_dimension=len(embedding)
            )

            return embedding

        except openai.RateLimitError as e:
            logger.error("OpenAI rate limit exceeded", error=str(e))
            raise Exception("Embedding service temporarily unavailable. Please try again.") from e

        except openai.APIError as e:
            logger.error("OpenAI API error", error=str(e))
            raise Exception("Failed to generate embedding. Please try again.") from e

        except Exception as e:
            logger.error("Unexpected error generating embedding", error=str(e), exc_info=True)
            raise Exception("Failed to generate embedding") from e

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a single batch request.
        More efficient than multiple individual calls.

        Args:
            texts: List of texts to generate embeddings for

        Returns:
            List of embedding vectors, one for each input text

        Raises:
            Exception: If embedding generation fails
        """
        try:
            # Clean up texts
            cleaned_texts = []
            for text in texts:
                cleaned = " ".join(text.split())
                if len(cleaned) > 8000:
                    cleaned = cleaned[:8000]
                cleaned_texts.append(cleaned)

            # Call OpenAI embeddings API with batch
            response = await self.client.embeddings.create(
                input=cleaned_texts,
                model=self.model
            )

            # Extract embeddings in order
            embeddings = [data.embedding for data in response.data]

            logger.info(
                "Generated batch embeddings",
                batch_size=len(texts),
                embedding_dimension=len(embeddings[0]) if embeddings else 0
            )

            return embeddings

        except openai.RateLimitError as e:
            logger.error("OpenAI rate limit exceeded for batch", error=str(e))
            raise Exception("Embedding service temporarily unavailable. Please try again.") from e

        except openai.APIError as e:
            logger.error("OpenAI API error for batch", error=str(e))
            raise Exception("Failed to generate embeddings. Please try again.") from e

        except Exception as e:
            logger.error("Unexpected error generating batch embeddings", error=str(e), exc_info=True)
            raise Exception("Failed to generate embeddings") from e


# Global singleton instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """
    Get the global embedding service instance (singleton pattern).

    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


__all__ = ["EmbeddingService", "get_embedding_service"]
