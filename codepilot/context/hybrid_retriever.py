"""
Hybrid Retriever - Combines BM25 and Embeddings using Reciprocal Rank Fusion

RRF (Reciprocal Rank Fusion) solves the problem of merging ranked lists
with different score scales by using ranks instead of raw scores.
"""

from typing import List, Dict, Any
from codepilot.context.bm25_retriever import BM25Retriever
from codepilot.context.embedding_retriever import EmbeddingRetriever


class HybridRetriever:
    """
    Combines keyword search (BM25) and semantic search (Embeddings).

    Why hybrid?
    - BM25 finds exact matches (function names, variable names)
    - Embeddings find semantic matches (related concepts)
    - Together they cover both precision and recall
    """

    def __init__(self, bm25_weight: float = 0.5, embedding_weight: float = 0.5):
        """
        Initialize hybrid retriever with both search methods.

        Args:
            bm25_weight: Weight for BM25 scores (0-1, default 0.5)
            embedding_weight: Weight for embedding scores (0-1, default 0.5)
        """
        # Create both retrievers
        self.bm25 = BM25Retriever()
        self.embeddings = EmbeddingRetriever()

        # Weights (can be tuned based on your needs)
        self.bm25_weight = bm25_weight
        self.embedding_weight = embedding_weight

        # RRF constant (k=60 is standard in literature)
        self.k = 60

    def index_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Index documents in BOTH retrievers.

        This is the unified entry point - call this once and both
        BM25 and Embeddings get indexed automatically.

        Args:
            documents: List of code chunks with metadata

        Returns:
            Statistics from both indexers
        """
        bm25_count = self.bm25.index_documents(documents)
        embedding_count = self.embeddings.index_documents(documents)

        return {
            'bm25_indexed': bm25_count,
            'embedding_indexed': embedding_count
        }

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search using both BM25 and Embeddings, merge with RRF.

        Process:
        1. Get results from both retrievers
        2. Convert to rank maps (doc_id → rank)
        3. Calculate RRF score for each unique document
        4. Sort by RRF score and return top K

        Args:
            query: Search query (natural language or code terms)
            top_k: Number of final results to return

        Returns:
            Merged results sorted by RRF score
        """
        # Step 1: Get results from BOTH retrievers
        # We fetch 2x top_k to have more candidates for fusion
        bm25_results = self.bm25.search(query, top_k=top_k * 2)
        embedding_results = self.embeddings.search(query, top_k=top_k * 2)

        # Step 2: Build rank maps (document ID → rank position)
        bm25_ranks = {}
        for i, result in enumerate(bm25_results):
            # Create unique ID from file + name
            doc_id = f"{result['file']}::{result['name']}"
            bm25_ranks[doc_id] = i + 1  # Ranks start at 1, not 0

        embedding_ranks = {}
        for i, result in enumerate(embedding_results):
            doc_id = f"{result['file']}::{result['name']}"
            embedding_ranks[doc_id] = i + 1

        # Step 3: Collect ALL unique documents from both lists
        all_doc_ids = set(bm25_ranks.keys()) | set(embedding_ranks.keys())

        # Step 4: Calculate RRF score for each document
        rrf_scores = {}
        for doc_id in all_doc_ids:
            score = 0.0

            # Add BM25 contribution (if document appeared in BM25 results)
            if doc_id in bm25_ranks:
                # RRF formula: 1 / (k + rank)
                score += self.bm25_weight * (1 / (self.k + bm25_ranks[doc_id]))

            # Add Embedding contribution (if document appeared in Embedding results)
            if doc_id in embedding_ranks:
                score += self.embedding_weight * (1 / (self.k + embedding_ranks[doc_id]))

            rrf_scores[doc_id] = score

        # Step 5: Sort by RRF score (highest first) and take top K
        sorted_doc_ids = sorted(
            rrf_scores.keys(),
            key=lambda doc_id: rrf_scores[doc_id],
            reverse=True
        )[:top_k]

        # Step 6: Build final results with metadata
        results = []
        for rank, doc_id in enumerate(sorted_doc_ids):
            # Get metadata from whichever retriever had this document
            metadata = self._get_metadata(doc_id, bm25_results, embedding_results)

            results.append({
                'rank': rank + 1,
                'rrf_score': round(rrf_scores[doc_id], 4),
                'in_bm25': doc_id in bm25_ranks,
                'in_embeddings': doc_id in embedding_ranks,
                'bm25_rank': bm25_ranks.get(doc_id, None),
                'embedding_rank': embedding_ranks.get(doc_id, None),
                **metadata
            })

        return results

    def _get_metadata(
        self,
        doc_id: str,
        bm25_results: List[Dict],
        embedding_results: List[Dict]
    ) -> Dict[str, Any]:
        """
        Extract metadata for a document from whichever list contains it.

        Args:
            doc_id: Document identifier (file::name)
            bm25_results: Results from BM25 search
            embedding_results: Results from embedding search

        Returns:
            Metadata dict with file, name, content, etc.
        """
        # Try BM25 results first
        for result in bm25_results:
            if f"{result['file']}::{result['name']}" == doc_id:
                return {
                    'file': result['file'],
                    'name': result['name'],
                    'type': result.get('type', 'unknown'),
                    'content': result.get('content', ''),
                    'start_line': result.get('start_line', 0),
                    'end_line': result.get('end_line', 0)
                }

        # Try embedding results
        for result in embedding_results:
            if f"{result['file']}::{result['name']}" == doc_id:
                return {
                    'file': result['file'],
                    'name': result['name'],
                    'type': result.get('type', 'unknown'),
                    'content': result.get('content', ''),
                    'start_line': result.get('start_line', 0),
                    'end_line': result.get('end_line', 0)
                }

        # Shouldn't happen, but return empty dict as fallback
        return {}

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from both retrievers."""
        return {
            'bm25': self.bm25.get_stats(),
            'embeddings': self.embeddings.get_stats(),
            'weights': {
                'bm25': self.bm25_weight,
                'embeddings': self.embedding_weight
            }
        }
