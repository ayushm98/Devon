"""
BM25 Retriever - Keyword-based code search

BM25 (Best Matching 25) is a ranking function that scores documents by:
1. Term Frequency (TF) - How often the search term appears in a document
2. Inverse Document Frequency (IDF) - Rarer terms get higher scores
3. Document Length Normalization - Longer docs don't unfairly dominate

This is the "keyword" half of our hybrid retrieval system.
"""

import re
from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi


class CodeTokenizer:
    """
    Tokenize code for searchability.

    Handles:
    - camelCase: getUserById -> get, user, by, id
    - snake_case: get_user_by_id -> get, user, by, id
    - Removes common Python keywords (they appear everywhere, low signal)
    """

    # Python keywords that appear in almost every file (low IDF = useless for search)
    STOP_WORDS = {
        'def', 'class', 'return', 'self', 'if', 'else', 'elif', 'for', 'while',
        'try', 'except', 'finally', 'with', 'as', 'import', 'from', 'in', 'is',
        'not', 'and', 'or', 'none', 'true', 'false', 'pass', 'break', 'continue',
        'lambda', 'yield', 'raise', 'assert', 'global', 'nonlocal', 'del',
        'the', 'a', 'an', 'of', 'to', 'args', 'kwargs', 'init', 'str', 'int',
        'list', 'dict', 'bool', 'float', 'type', 'any', 'optional'
    }

    def tokenize(self, text: str) -> List[str]:
        """
        Convert code text into searchable tokens.

        Example:
            "def getUserById(user_id):" -> ['get', 'user', 'by', 'id', 'user', 'id']
        """
        # Step 1: Split camelCase and PascalCase
        # "getUserById" -> "get User By Id"
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

        # Step 2: Split snake_case and other separators
        # "get_user_by_id" -> "get user by id"
        text = re.sub(r'[_\-./\\(){}[\]:,;"\']', ' ', text)

        # Step 3: Lowercase and split into words
        words = text.lower().split()

        # Step 4: Remove stop words and very short tokens (1-2 chars)
        tokens = [
            word for word in words
            if word not in self.STOP_WORDS and len(word) > 2
        ]

        return tokens


class BM25Retriever:
    """
    BM25-based code search.

    How it works:
    1. Index: Convert each code chunk into tokens, build BM25 index
    2. Search: Tokenize query, score each document, return top-K
    """

    def __init__(self):
        self.tokenizer = CodeTokenizer()
        self.documents = []      # List of original documents
        self.doc_tokens = []     # List of tokenized documents
        self.bm25 = None         # BM25 index (built after indexing)
        self.doc_metadata = []   # Metadata for each document (file path, line numbers, etc.)

    def index_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        Build BM25 index from code documents.

        Args:
            documents: List of dicts with 'content' and optional metadata
                       Example: {'content': 'def get_user()...', 'file': 'users.py', 'type': 'function'}

        Returns:
            Number of documents indexed
        """
        self.documents = []
        self.doc_tokens = []
        self.doc_metadata = []

        for doc in documents:
            content = doc.get('content', '')

            # Tokenize the content
            tokens = self.tokenizer.tokenize(content)

            # Only index if we got meaningful tokens
            if tokens:
                self.documents.append(content)
                self.doc_tokens.append(tokens)
                self.doc_metadata.append({
                    'file': doc.get('file', 'unknown'),
                    'name': doc.get('name', 'unknown'),
                    'type': doc.get('type', 'unknown'),
                    'start_line': doc.get('start_line', 0),
                    'end_line': doc.get('end_line', 0)
                })

        # Build BM25 index from tokenized documents
        if self.doc_tokens:
            self.bm25 = BM25Okapi(self.doc_tokens)

        return len(self.documents)

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for relevant code using BM25 scoring.

        Args:
            query: Search query (natural language or code terms)
            top_k: Number of results to return

        Returns:
            List of results with scores and metadata, sorted by relevance
        """
        if not self.bm25:
            return []

        # Tokenize the query the same way we tokenized documents
        query_tokens = self.tokenizer.tokenize(query)

        if not query_tokens:
            return []

        # Get BM25 scores for all documents
        scores = self.bm25.get_scores(query_tokens)

        # Get top-K document indices (sorted by score descending)
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        # Build results with scores and metadata
        results = []
        for rank, idx in enumerate(top_indices):
            if scores[idx] > 0:  # Only include if there's some match
                results.append({
                    'rank': rank + 1,
                    'score': float(scores[idx]),
                    'content': self.documents[idx],
                    **self.doc_metadata[idx]
                })

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the index."""
        if not self.doc_tokens:
            return {'indexed': False}

        total_tokens = sum(len(tokens) for tokens in self.doc_tokens)
        avg_tokens = total_tokens / len(self.doc_tokens) if self.doc_tokens else 0

        return {
            'indexed': True,
            'num_documents': len(self.documents),
            'total_tokens': total_tokens,
            'avg_tokens_per_doc': round(avg_tokens, 2)
        }
