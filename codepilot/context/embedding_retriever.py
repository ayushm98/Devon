"""
Embedding Retriever - Semantic code search using vector embeddings

How it works:
1. Use a pre-trained model to convert code → vectors (embeddings)
2. Store vectors in ChromaDB (a vector database)
3. When searching, convert query → vector, find similar vectors

This is the "semantic" half of our hybrid retrieval system.
"""

import os
from typing import List, Dict, Any, Optional

# ChromaDB for vector storage and similarity search
import chromadb
from chromadb.config import Settings

# Sentence Transformers for creating embeddings
# (Same pattern as our simple example: model.encode(text) → vector)
from sentence_transformers import SentenceTransformer


class EmbeddingRetriever:
    """
    Semantic search using vector embeddings.

    Pattern from our example:
        model.encode("login auth") → [0.2, 0.8, ...]

    But instead of manual cosine_similarity, ChromaDB does it efficiently.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        persist_directory: str = ".codepilot_cache/chromadb"
    ):
        """
        Initialize the embedding retriever.

        Args:
            model_name: Which sentence-transformer model to use
                        "all-MiniLM-L6-v2" is small (80MB) but effective
            persist_directory: Where to save the vector database
        """
        # Load the pre-trained model (same as example: SentenceTransformer(...))
        self.model = SentenceTransformer(model_name)

        # Create ChromaDB client
        # persist_directory means vectors are saved to disk (survives restarts)
        os.makedirs(persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Get or create a "collection" (like a table in a database)
        # This is where we store our code vectors
        self.collection = self.client.get_or_create_collection(
            name="code_embeddings",
            metadata={"description": "Code chunks for semantic search"}
        )

    def index_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        Convert code chunks to vectors and store in ChromaDB.

        This is like our example:
            vec = model.encode(text)
        But we store many vectors at once in a database.

        Args:
            documents: List of dicts with 'content' and metadata
                      Example: {'content': 'def login()...', 'file': 'auth.py'}

        Returns:
            Number of documents indexed
        """
        if not documents:
            return 0

        # Prepare data for ChromaDB
        ids = []           # Unique ID for each document
        texts = []         # The actual code content
        metadatas = []     # Extra info (file path, line numbers, etc.)

        for i, doc in enumerate(documents):
            content = doc.get('content', '')
            if not content.strip():
                continue

            # Create unique ID (ChromaDB requires string IDs)
            doc_id = f"{doc.get('file', 'unknown')}::{doc.get('name', i)}"

            ids.append(doc_id)
            texts.append(content)
            metadatas.append({
                'file': doc.get('file', 'unknown'),
                'name': doc.get('name', 'unknown'),
                'type': doc.get('type', 'unknown'),
                'start_line': doc.get('start_line', 0),
                'end_line': doc.get('end_line', 0)
            })

        if not texts:
            return 0

        # Generate embeddings for all texts at once
        # (Same as example: model.encode(text), but batched for efficiency)
        embeddings = self.model.encode(texts, show_progress_bar=False)

        # Store in ChromaDB
        # ChromaDB handles: storing vectors, building search index, similarity math
        self.collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),  # ChromaDB wants Python lists
            documents=texts,
            metadatas=metadatas
        )

        return len(texts)

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Find code semantically similar to the query.

        This is like our example:
            query_vec = model.encode(query)
            similarity = cosine_similarity(query_vec, stored_vecs)
        But ChromaDB does the similarity search efficiently.

        Args:
            query: Natural language or code description
            top_k: Number of results to return

        Returns:
            List of results with similarity scores and metadata
        """
        # Convert query to vector (same as example: model.encode(...))
        query_embedding = self.model.encode(query)

        # ChromaDB finds the most similar stored vectors
        # Internally, it computes cosine similarity against all stored vectors
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )

        # Format results
        # Note: ChromaDB returns "distances" (lower = more similar)
        # We convert to "scores" (higher = more similar) for consistency with BM25
        formatted = []

        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                # Convert distance to similarity score (1 - distance for cosine)
                distance = results['distances'][0][i]
                similarity = 1 - distance  # Higher = more similar

                formatted.append({
                    'rank': i + 1,
                    'score': float(similarity),
                    'content': results['documents'][0][i],
                    **results['metadatas'][0][i]
                })

        return formatted

    def clear_index(self):
        """Remove all documents from the index."""
        # Delete and recreate the collection
        self.client.delete_collection("code_embeddings")
        self.collection = self.client.get_or_create_collection(
            name="code_embeddings",
            metadata={"description": "Code chunks for semantic search"}
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the index."""
        count = self.collection.count()
        return {
            'indexed': count > 0,
            'num_documents': count,
            'model': 'all-MiniLM-L6-v2',
            'embedding_dimension': 384
        }
