"""
Vector Database Service
========================
Manages menu item embeddings and semantic search using ChromaDB.

ChromaDB stores embeddings locally (no extra infrastructure needed).
Uses ChromaDB's built-in default embedding function (ONNX all-MiniLM-L6-v2).
Provides semantic search for menu items with spelling tolerance and synonym understanding.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import structlog
from pathlib import Path

logger = structlog.get_logger("ai_services.vector_db")


class VectorDBService:
    """
    Manages vector embeddings for semantic menu search.

    Uses ChromaDB for local vector storage (persists to disk).
    Uses ChromaDB's built-in default embedding function (no extra dependencies).
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
        # ChromaDB uses its built-in default embedding function automatically
        self.menu_collection = self.client.get_or_create_collection(
            name="menu_items",
            metadata={
                "hnsw:space": "cosine",
            }
        )

        logger.info(
            "VectorDBService initialized",
            collection_count=self.menu_collection.count(),
            storage_path=str(storage_path),
            embedding_model="chromadb-default (ONNX all-MiniLM-L6-v2)"
        )

    async def bulk_index_menu_items(self, items: List[Dict[str, Any]]):
        """
        Index multiple menu items. ChromaDB generates embeddings from documents.
        """
        try:
            ids = []
            documents = []
            metadatas = []

            for item in items:
                ids.append(str(item['id']))
                documents.append(
                    f"{item['name']}. {item.get('description', '')}. Category: {item['category']}"
                )
                metadatas.append({
                    "name": item['name'],
                    "description": item.get('description', ''),
                    "category": item['category'],
                    "price": item['price'],
                })

            # ChromaDB auto-generates embeddings from documents
            self.menu_collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )

            logger.info(
                "Bulk indexed menu items",
                count=len(items),
                total_in_collection=self.menu_collection.count()
            )

        except Exception as e:
            logger.error("Failed to bulk index menu items", error=str(e), exc_info=True)
            raise

    async def semantic_search(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.85,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search menu items semantically. ChromaDB generates query embedding automatically.
        """
        try:
            where_filter = None
            if category_filter:
                where_filter = {"category": category_filter}

            # Use query_texts — chromadb generates embedding automatically
            results = self.menu_collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter,
                include=["metadatas", "distances"]
            )

            items = []
            if results and results['ids'] and len(results['ids']) > 0:
                for idx, item_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][idx]
                    similarity = 1 - (distance / 2)

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
                    })

            logger.info(
                "Semantic search completed",
                query=query[:50],
                results_count=len(items),
                top_similarity=items[0]['similarity_score'] if items else 0
            )

            return items

        except Exception as e:
            logger.error("Semantic search failed", query=query, error=str(e), exc_info=True)
            return []

    def clear_collection(self):
        """Clear all items from collection (use for fresh re-indexing)."""
        try:
            self.client.delete_collection("menu_items")
            self.menu_collection = self.client.create_collection(
                name="menu_items",
                metadata={"hnsw:space": "cosine"}
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
