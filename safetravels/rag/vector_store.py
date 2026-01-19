#!/usr/bin/env python3
"""
SafeTravels RAG - Vector Store
==============================

This module provides the ChromaDB vector store implementation for the
SafeTravels RAG (Retrieval-Augmented Generation) pipeline.

The VectorStore class manages document storage and semantic search for:
    - Crime statistics (state and county level)
    - Truck stop locations with safety ratings
    - Theft reports and alerts
    - Analysis documents (time patterns, commodities, methods)

Usage:
    from safetravels.rag.vector_store import get_vector_store
    
    store = get_vector_store()
    results = store.query("Texas cargo theft I-35")

Author: SafeTravels Team
Created: January 2026
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
import logging
from pathlib import Path
from safetravels.core.app_settings import settings

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

# Collection names for different data types
COLLECTION_NAMES = {
    'CRIME_DATA': 'crime_data',
    'THEFT_REPORTS': 'theft_reports',
    'TRUCK_STOPS': 'truck_stops',
    'NEWS': 'news',
    'MAIN': 'safetravels_main'
}

# Default number of results to return from queries
DEFAULT_QUERY_RESULTS = 5

# Similarity metric for vector comparisons
SIMILARITY_METRIC = 'cosine'


# =============================================================================
# VECTOR STORE CLASS
# =============================================================================

class VectorStore:
    """
    ChromaDB vector store for RAG document retrieval.
    
    This class provides methods to:
        - Store documents with metadata as vector embeddings
        - Query for semantically similar documents
        - Manage multiple collections for different data types
    
    The vector store uses ChromaDB's built-in embedding function to convert
    text documents into vectors for similarity search.
    
    Attributes:
        persist_dir: Directory path for persistent storage
        client: ChromaDB client instance
        collections: Dictionary of named collections
        main_collection: Unified collection for cross-type search
    
    Example:
        store = VectorStore()
        store.add_documents(
            documents=["Texas has high cargo theft rates"],
            metadatas=[{"state": "TX", "type": "crime_data"}],
            ids=["doc-001"],
            collection_name="crime_data"
        )
        results = store.query("Texas theft statistics")
    """
    
    def __init__(self, persist_dir: Optional[str] = None) -> None:
        """
        Initialize the ChromaDB vector store connection.
        
        Args:
            persist_dir: Optional custom directory for database persistence.
                         Defaults to settings.chroma_persist_dir.
        """
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        
        logger.info(f"Initializing ChromaDB at: {self.persist_dir}")
        
        # Create persistent ChromaDB client with telemetry disabled
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize collections for different data types
        self.collections: Dict[str, Any] = {
            COLLECTION_NAMES['CRIME_DATA']: self._create_collection(COLLECTION_NAMES['CRIME_DATA']),
            COLLECTION_NAMES['THEFT_REPORTS']: self._create_collection(COLLECTION_NAMES['THEFT_REPORTS']),
            COLLECTION_NAMES['TRUCK_STOPS']: self._create_collection(COLLECTION_NAMES['TRUCK_STOPS']),
            COLLECTION_NAMES['NEWS']: self._create_collection(COLLECTION_NAMES['NEWS']),
        }
        
        # Main collection for unified cross-type search
        self.main_collection = self._create_collection(COLLECTION_NAMES['MAIN'])
        
        logger.info("ChromaDB initialized successfully")
    
    def _create_collection(self, name: str) -> Any:
        """
        Get or create a ChromaDB collection with cosine similarity.
        
        Args:
            name: Name of the collection to create
            
        Returns:
            ChromaDB collection object
        """
        return self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": SIMILARITY_METRIC}
        )
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        collection_name: str = COLLECTION_NAMES['MAIN']
    ) -> None:
        """
        Add documents to a collection with automatic embedding.
        
        Documents are automatically embedded using ChromaDB's default
        embedding function and stored in both the specified collection
        and the main collection for unified search.
        
        Args:
            documents: List of text documents to store
            metadatas: List of metadata dictionaries for each document.
                      Should include fields like 'source', 'type', 'state', etc.
            ids: List of unique identifiers for each document
            collection_name: Target collection name (default: main collection)
            
        Raises:
            ValueError: If documents, metadatas, and ids have different lengths
        
        Example:
            store.add_documents(
                documents=["Dallas County has high theft rates"],
                metadatas=[{"county": "Dallas", "state": "TX", "type": "county_detail"}],
                ids=["county-dallas"],
                collection_name="crime_data"
            )
        """
        if not (len(documents) == len(metadatas) == len(ids)):
            raise ValueError("documents, metadatas, and ids must have the same length")
        
        # Get the target collection
        collection = self.collections.get(collection_name, self.main_collection)
        
        # Add documents to the specific collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        # Also add to main collection for unified search (if not already main)
        if collection_name != COLLECTION_NAMES['MAIN']:
            main_ids = [f"main_{doc_id}" for doc_id in ids]
            self.main_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=main_ids
            )
        
        logger.debug(f"Added {len(documents)} documents to collection '{collection_name}'")
    
    def query(
        self,
        query_text: str,
        n_results: int = DEFAULT_QUERY_RESULTS,
        collection_name: str = COLLECTION_NAMES['MAIN'],
        where_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List]:
        """
        Query the vector store for semantically similar documents.
        
        Uses ChromaDB's embedding function to convert the query text
        into a vector and finds the most similar documents.
        
        Args:
            query_text: The search query in natural language
            n_results: Maximum number of results to return (default: 5)
            collection_name: Which collection to search (default: main)
            where_filter: Optional metadata filter for narrowing results.
                         Example: {"state": "TX"} to only get Texas documents
            
        Returns:
            Dictionary containing:
                - documents: List of matching document texts
                - metadatas: List of metadata dictionaries
                - distances: List of similarity distances (lower = more similar)
                - ids: List of document IDs
                
        Example:
            results = store.query(
                query_text="safe truck stops near Dallas",
                n_results=10,
                where_filter={"state": "TX"}
            )
            for doc, meta in zip(results['documents'], results['metadatas']):
                print(f"{meta['name']}: {doc[:100]}...")
        """
        collection = self.collections.get(collection_name, self.main_collection)
        
        raw_results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_filter
        )
        
        # Flatten results (ChromaDB returns nested lists for batch queries)
        return {
            'documents': raw_results['documents'][0] if raw_results['documents'] else [],
            'metadatas': raw_results['metadatas'][0] if raw_results['metadatas'] else [],
            'distances': raw_results['distances'][0] if raw_results['distances'] else [],
            'ids': raw_results['ids'][0] if raw_results['ids'] else []
        }
    
    def query_by_location(
        self,
        latitude: float,
        longitude: float,
        n_results: int = DEFAULT_QUERY_RESULTS
    ) -> Dict[str, List]:
        """
        Query for documents relevant to a specific geographic location.
        
        Creates a location-aware query to find nearby truck stops,
        local crime data, and area-specific theft reports.
        
        Args:
            latitude: GPS latitude coordinate
            longitude: GPS longitude coordinate
            n_results: Maximum number of results to return
            
        Returns:
            Dictionary with documents, metadatas, distances, and ids
            
        Note:
            This uses semantic search on the coordinates, not actual
            geospatial distance calculations. For precise location
            matching, use metadata filters.
        """
        query = f"cargo theft risk near latitude {latitude} longitude {longitude}"
        return self.query(query, n_results)
    
    def get_collection_stats(self) -> Dict[str, int]:
        """
        Get document counts for all collections.
        
        Returns:
            Dictionary mapping collection names to document counts
            
        Example:
            stats = store.get_collection_stats()
            print(f"Crime data: {stats['crime_data']} documents")
            print(f"Truck stops: {stats['truck_stops']} documents")
        """
        stats = {}
        
        for collection_name, collection in self.collections.items():
            stats[collection_name] = collection.count()
        
        stats['main'] = self.main_collection.count()
        
        return stats
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection from the database.
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            True if deleted successfully, False if collection didn't exist
        """
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as error:
            logger.warning(f"Could not delete collection '{collection_name}': {error}")
            return False
    
    def clear_all(self) -> None:
        """
        Clear all collections from the database.
        
        WARNING: This permanently deletes all stored documents!
        Use with caution - primarily for testing and development.
        """
        logger.warning("Clearing all collections from vector store")
        
        for collection_name in list(self.collections.keys()):
            self.delete_collection(collection_name)
        
        self.delete_collection(COLLECTION_NAMES['MAIN'])
        
        logger.info("All collections cleared")


# =============================================================================
# SINGLETON PATTERN
# =============================================================================

# Global singleton instance
_vector_store_instance: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """
    Get or create the singleton VectorStore instance.
    
    This ensures only one ChromaDB connection is created and reused
    throughout the application lifecycle.
    
    Returns:
        VectorStore singleton instance
        
    Example:
        store = get_vector_store()
        results = store.query("Texas cargo theft")
    """
    global _vector_store_instance
    
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    
    return _vector_store_instance


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    """Test the vector store connection and basic operations."""
    
    print("=" * 50)
    print("Vector Store Connection Test")
    print("=" * 50)
    
    # Get vector store instance
    store = get_vector_store()
    
    # Display collection statistics
    stats = store.get_collection_stats()
    print("\n📊 Collection Statistics:")
    for collection_name, document_count in stats.items():
        print(f"  {collection_name}: {document_count} documents")
    
    # Test a sample query
    print("\n🔍 Testing Sample Query:")
    query = "Texas cargo theft"
    results = store.query(query, n_results=3)
    
    print(f"  Query: '{query}'")
    print(f"  Results: {len(results['documents'])} documents found")
    
    for i, metadata in enumerate(results['metadatas']):
        doc_type = metadata.get('type', 'unknown')
        state = metadata.get('state', 'N/A')
        print(f"    {i+1}. {doc_type} - {state}")
    
    print("\n✅ Vector store test complete!")
