"""
Vector Database Service
========================
Manages menu item embeddings and semantic search using ChromaDB.

ChromaDB stores embeddings locally (no extra infrastructure needed).
Provides semantic search for menu items with spelling tolerance and synonym understanding.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import structlog
from pathlib import Path

from app.core.config import config
# Use local embeddings instead of OpenAI
from app.ai_services.local_embedding_service import get_local_embedding_service

logger = structlog.get_logger("ai_services.vector_db")


class VectorDBService:
    """
    Manages vector embeddings for semantic menu search.

    Uses ChromaDB for local vector storage (persists to disk).
    Uses local Sentence Transformers for embeddings (no OpenAI API needed).
    """

    def __init__(self):
        # Create persistent storage directory
        storage_path = Path("data/chromadb")
        storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=str(storage_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create menu items collection
        self.menu_collection = self.client.get_or_create_collection(
            name="menu_items",
            metadata={
                "hnsw:space": "cosine",  # Cosine similarity for embeddings
                "description": "Restaurant menu items with TRUE semantic search using local embeddings"
            }
        )

        # Use local embedding service (no API costs, works offline)
        self.embedding_service = get_local_embedding_service()

        logger.info(
            "VectorDBService initialized with LOCAL embeddings",
            collection_count=self.menu_collection.count(),
            storage_path=str(storage_path),
            embedding_model="sentence-transformers (local)"
        )

    async def index_menu_item(
        self,
        item_id: str,
        name: str,
        description: str,
        category: str,
        price: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Index a single menu item with its embedding.

        Args:
            item_id: Unique item ID
            name: Item name (e.g., "Butter Chicken")
            description: Item description
            category: Category name
            price: Item price
            metadata: Additional metadata (dietary info, spice level, etc.)
        """
        try:
            # Create rich text for embedding (captures semantics)
            # Include name, description, and category for better matching
            embedding_text = f"{name}. {description}. Category: {category}"

            # Generate embedding using local Sentence Transformers (synchronous call)
            embedding = self.embedding_service.generate_embedding(embedding_text)

            # Prepare metadata
            item_metadata = {
                "name": name,
                "description": description,
                "category": category,
                "price": price
            }
            if metadata:
                item_metadata.update(metadata)

            # Add to ChromaDB
            self.menu_collection.add(
                ids=[str(item_id)],
                embeddings=[embedding],
                documents=[embedding_text],
                metadatas=[item_metadata]
            )

            logger.info(
                "Menu item indexed",
                item_id=item_id,
                name=name
            )

        except Exception as e:
            logger.error(
                "Failed to index menu item",
                item_id=item_id,
                name=name,
                error=str(e),
                exc_info=True
            )
            raise

    async def bulk_index_menu_items(self, items: List[Dict[str, Any]]):
        """
        Efficiently index multiple menu items at once.

        Args:
            items: List of dicts with keys: id, name, description, category, price, metadata
        """
        try:
            # Prepare batch data
            ids = []
            documents = []
            metadatas = []

            # Generate embeddings in batch (more efficient)
            embedding_texts = []
            for item in items:
                text = f"{item['name']}. {item['description']}. Category: {item['category']}"
                embedding_texts.append(text)

            # Batch generate embeddings (synchronous call)
            embeddings = self.embedding_service.generate_embeddings_batch(embedding_texts)

            # Prepare ChromaDB data
            for item, embedding, text in zip(items, embeddings, embedding_texts):
                ids.append(str(item['id']))
                documents.append(text)

                metadata = {
                    "name": item['name'],
                    "description": item.get('description', ''),
                    "category": item['category'],
                    "price": item['price']
                }
                # Merge additional metadata if provided
                if 'metadata' in item and item['metadata']:
                    metadata.update(item['metadata'])

                metadatas.append(metadata)

            # Bulk add to ChromaDB
            self.menu_collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )

            logger.info(
                "Bulk indexed menu items",
                count=len(items),
                total_in_collection=self.menu_collection.count()
            )

        except Exception as e:
            logger.error(
                "Failed to bulk index menu items",
                error=str(e),
                exc_info=True
            )
            raise

    async def semantic_search(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.6,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search menu items semantically (understands meaning, not just keywords).

        Args:
            query: User's search query (e.g., "something spicy", "creamy chicken")
            limit: Maximum results to return
            min_similarity: Minimum cosine similarity (0-1)
            category_filter: Optional category filter

        Returns:
            List of matching items with similarity scores
        """
        try:
            # Generate embedding for query (synchronous call)
            query_embedding = self.embedding_service.generate_embedding(query)

            # Build where filter if category specified
            where_filter = None
            if category_filter:
                where_filter = {"category": category_filter}

            # Query ChromaDB
            results = self.menu_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )

            # Convert to friendly format
            items = []
            if results and results['ids'] and len(results['ids']) > 0:
                for idx, item_id in enumerate(results['ids'][0]):
                    # ChromaDB returns distance, convert to similarity score
                    # Distance: 0 = identical, 2 = opposite
                    # Similarity: 1 = identical, 0 = opposite
                    distance = results['distances'][0][idx]
                    similarity = 1 - (distance / 2)  # Normalize to 0-1

                    # Filter by minimum similarity
                    if similarity < min_similarity:
                        continue

                    metadata = results['metadatas'][0][idx]

                    items.append({
                        'id': item_id,
                        'name': metadata['name'],
                        'description': metadata.get('description', ''),
                        'category': metadata['category'],
                        'price': metadata['price'],
                        'similarity_score': round(similarity, 3),
                        'match_reason': self._generate_match_reason(similarity)
                    })

            logger.info(
                "Semantic search completed",
                query=query[:50],
                results_count=len(items),
                top_similarity=items[0]['similarity_score'] if items else 0
            )

            return items

        except Exception as e:
            logger.error(
                "Semantic search failed",
                query=query,
                error=str(e),
                exc_info=True
            )
            # Return empty list instead of raising (graceful degradation)
            return []

    def _generate_match_reason(self, similarity: float) -> str:
        """Generate human-readable explanation for match quality."""
        if similarity >= 0.9:
            return "Excellent match"
        elif similarity >= 0.8:
            return "Great match"
        elif similarity >= 0.7:
            return "Good match"
        elif similarity >= 0.6:
            return "Relevant match"
        else:
            return "Weak match"

    def clear_collection(self):
        """Clear all items from collection (use for fresh re-indexing)."""
        try:
            self.client.delete_collection("menu_items")
            self.menu_collection = self.client.create_collection(
                name="menu_items",
                metadata={
                    "hnsw:space": "cosine",
                    "description": "Restaurant menu items with semantic search"
                }
            )
            logger.info("Menu collection cleared")
        except Exception as e:
            logger.error("Failed to clear collection", error=str(e))
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        return {
            "total_items": self.menu_collection.count(),
            "collection_name": self.menu_collection.name,
            "storage_type": "persistent"
        }


# Global singleton instance
_vector_db_service = None


def get_vector_db_service() -> VectorDBService:
    """Get the global VectorDBService instance (singleton pattern)."""
    global _vector_db_service
    if _vector_db_service is None:
        _vector_db_service = VectorDBService()
    return _vector_db_service


__all__ = ["VectorDBService", "get_vector_db_service"]
