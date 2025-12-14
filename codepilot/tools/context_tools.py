"""
Context Tools
Tools that use the codebase index and dependency graph
"""

from codepilot.context.indexer import CodebaseIndexer
from codepilot.context.selector import ContextSelector
from codepilot.context.hybrid_retriever import HybridRetriever
from typing import List, Dict, Any

# Global instances (set when index_codebase is called)
_indexer = None
_selector = None
_hybrid_retriever = None  # Will hold our search engine


def index_codebase(path: str = ".") -> str:
    """
    Index a codebase to enable context-aware tools.

    This builds THREE indexes:
    1. CodebaseIndexer - AST-based parsing of all files
    2. ContextSelector - Dependency graph
    3. HybridRetriever - BM25 + Embeddings for search

    Args:
        path: Root directory to index (default: current directory)

    Returns:
        Summary of what was indexed
    """
    global _indexer, _selector, _hybrid_retriever

    # Step 1: Create indexer and build AST index
    _indexer = CodebaseIndexer(path)
    stats = _indexer.build_index()

    # Step 2: Create selector and build dependency graph
    _selector = ContextSelector(_indexer)
    _selector.build_dependency_graph()

    # Step 3: Build hybrid retriever index
    # Convert indexed data to documents for retrieval
    documents = []
    for file_path, file_data in _indexer.index.items():
        # Read the source file to extract code snippets
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_lines = f.readlines()
        except:
            continue  # Skip if file can't be read

        # Add each function as a searchable document
        for func in file_data.get('functions', []):
            start = func.get('start_line', 1) - 1  # Convert to 0-indexed
            end = func.get('end_line', start + 1)

            # Extract code lines
            code = ''.join(source_lines[start:end])

            if code.strip():  # Only add if we got code
                documents.append({
                    'content': code,
                    'file': file_path,
                    'name': func['name'],
                    'type': 'function',
                    'start_line': func.get('start_line', 0),
                    'end_line': func.get('end_line', 0)
                })

        # Add each class as a searchable document
        for cls in file_data.get('classes', []):
            start = cls.get('start_line', 1) - 1
            end = cls.get('end_line', start + 1)

            code = ''.join(source_lines[start:end])

            if code.strip():
                documents.append({
                    'content': code,
                    'file': file_path,
                    'name': cls['name'],
                    'type': 'class',
                    'start_line': cls.get('start_line', 0),
                    'end_line': cls.get('end_line', 0)
                })

    # Create and index hybrid retriever
    _hybrid_retriever = HybridRetriever()
    retrieval_stats = _hybrid_retriever.index_documents(documents)

    # Return summary
    return (
        f"Indexed {stats['total_files']} files, "
        f"{stats['total_functions']} functions, "
        f"{stats['total_classes']} classes. "
        f"Dependency graph: {_selector.graph.number_of_edges()} connections. "
        f"Hybrid retriever: {retrieval_stats['bm25_indexed']} BM25 docs, "
        f"{retrieval_stats['embedding_indexed']} embedding docs."
    )


def search_codebase(query: str, top_k: int = 5) -> str:
    """
    Search the codebase using hybrid retrieval (BM25 + embeddings).

    Uses both keyword matching and semantic search to find relevant code.

    Args:
        query: What to search for (e.g., "authentication logic", "error handling")
        top_k: Number of results to return (default: 5)

    Returns:
        Formatted string with search results including file paths, function names, and code snippets
    """
    global _hybrid_retriever

    # Check if index is built
    if _hybrid_retriever is None:
        return "Error: Codebase not indexed. Call index_codebase() first."

    # Perform hybrid search
    results = _hybrid_retriever.search(query, top_k=top_k)

    if not results:
        return f"No results found for query: '{query}'"

    # Format results for the agent
    output = [f"Found {len(results)} results for '{query}':\n"]

    for result in results:
        output.append(f"\n[{result['rank']}] {result['type']}: {result['name']}")
        output.append(f"    File: {result['file']}:{result['start_line']}")
        output.append(f"    Score: {result['rrf_score']:.4f}")
        output.append(f"    In BM25: {result['in_bm25']}, In Embeddings: {result['in_embeddings']}")

        # Show code snippet (first 3 lines)
        code_lines = result['content'].split('\n')[:3]
        output.append(f"    Code preview:")
        for line in code_lines:
            output.append(f"      {line}")

    return '\n'.join(output)
