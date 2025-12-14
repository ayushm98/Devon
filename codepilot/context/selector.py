"""
Context Selector
Builds dependency graph and selects relevant code for LLM context
"""

import networkx as nx
from codepilot.context.indexer import CodebaseIndexer


class ContextSelector:
    """
    Select relevant code context based on dependencies
    """

    def __init__(self, indexer: CodebaseIndexer):
        """
        Initialize with a codebase indexer

        Args:
            indexer: CodebaseIndexer with already-built index
        """
        self.indexer = indexer          # Store the indexer (has all import data)
        self.graph = nx.DiGraph()       # Create empty directed graph

    def build_dependency_graph(self):
        """
        Build a directed graph where:
        - Each node is a file
        - Each edge A → B means "A imports from B"
        """
        # Loop through every file in the index
        for file_path, data in self.indexer.index.items():

            # Get imports for this file
            imports = data['imports']

            # Loop through each import
            for imp in imports:
                # Get the module name (e.g., 'codepilot.llm.client')
                module_name = imp.get('module', '')

                if module_name:
                    # Convert to file path: 'codepilot.llm.client' → 'codepilot/llm/client.py'
                    target_path = module_name.replace('.', '/') + '.py'

                    # Check if this file exists in our index
                    # (we only care about files in our project, not external like 'os' or 'json')
                    for indexed_file in self.indexer.index.keys():
                        if indexed_file.endswith(target_path):
                            # Add edge: file_path depends on indexed_file
                            self.graph.add_edge(file_path, indexed_file)
                            break

        print(f"Graph built: {self.graph.number_of_nodes()} files, {self.graph.number_of_edges()} dependencies")

    def get_dependencies(self, file_path: str) -> list:
        """
        Get all files that this file imports from

        Args:
            file_path: The file to check

        Returns:
            List of file paths that this file depends on
        """
        if file_path not in self.graph:
            return []
        return list(self.graph.successors(file_path))

    def get_dependents(self, file_path: str) -> list:
        """
        Get all files that import from this file

        Args:
            file_path: The file to check

        Returns:
            List of file paths that depend on this file
        """
        if file_path not in self.graph:
            return []
        return list(self.graph.predecessors(file_path))

    def get_related_files(self, file_path: str) -> list:
        """
        Get all files related to this file (both directions)

        Args:
            file_path: The file to check

        Returns:
            List of all related file paths
        """
        related = set()  # Use set to avoid duplicates

        # Files this one depends on
        related.update(self.get_dependencies(file_path))

        # Files that depend on this one
        related.update(self.get_dependents(file_path))

        return list(related)
