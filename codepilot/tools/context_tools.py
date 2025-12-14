"""
Context Tools
Tools that use the codebase index and dependency graph
"""

from codepilot.context.indexer import CodebaseIndexer
from codepilot.context.selector import ContextSelector

# Global instances (set when index_codebase is called)
_indexer = None
_selector = None


def index_codebase(path: str = ".") -> str:
    """
    Index a codebase to enable context-aware tools

    Args:
        path: Root directory to index (default: current directory)

    Returns:
        Summary of what was indexed
    """
    global _indexer, _selector

    # Create indexer and build index
    _indexer = CodebaseIndexer(path)
    stats = _indexer.build_index()

    # Create selector and build dependency graph
    _selector = ContextSelector(_indexer)
    _selector.build_dependency_graph()

    # Return summary
    return (
        f"Indexed {stats['total_files']} files, "
        f"{stats['total_functions']} functions, "
        f"{stats['total_classes']} classes. "
        f"Dependency graph: {_selector.graph.number_of_edges()} connections."
    )
