"""
Codebase Indexer
Scans entire project and builds searchable index of all Python files
"""

import os
import json
import hashlib
from typing import Dict, List, Any, Optional
from codepilot.context.parser import CodeParser


class CodebaseIndexer:
    """
    Index an entire codebase for fast retrieval
    """

    def __init__(self, root_path: str, cache_dir: str = ".codepilot_cache"):
        """
        Initialize indexer

        Args:
            root_path: Root directory to index
            cache_dir: Where to store cached index
        """
        self.root_path = root_path
        self.cache_dir = cache_dir
        self.parser = CodeParser()
        self.index = {}  # file_path -> parsed_data

    def build_index(self, file_extensions: List[str] = ['.py']) -> Dict[str, Any]:
        """
        Scan directory and index all matching files

        Args:
            file_extensions: List of extensions to index (default: ['.py'])

        Returns:
            Statistics about the indexing process
        """
        total_files = 0
        total_functions = 0
        total_classes = 0
        errors = []

        # Walk through directory tree
        for root, dirs, files in os.walk(self.root_path):
            # Skip unwanted directories (modify dirs in-place)
            dirs[:] = [d for d in dirs if d not in [
                '__pycache__', 'venv', 'node_modules', '.git',
                '.pytest_cache', '.mypy_cache'
            ]]

            # Process each file
            for file in files:
                # Check if file has matching extension
                if any(file.endswith(ext) for ext in file_extensions):
                    file_path = os.path.join(root, file)

                    # Parse the file
                    result = self.parser.parse_file(file_path)

                    if result.get('parse_errors'):
                        errors.append({
                            'file': file_path,
                            'error': result['parse_errors'][0]
                        })
                    else:
                        # Store in index
                        self.index[file_path] = result
                        total_files += 1
                        total_functions += len(result.get('functions', []))
                        total_classes += len(result.get('classes', []))

        return {
            'total_files': total_files,
            'total_functions': total_functions,
            'total_classes': total_classes,
            'errors': errors
        }

    def find_definition(self, name: str) -> List[Dict[str, Any]]:
        """
        Find where a function or class is defined

        Args:
            name: Function or class name to search for

        Returns:
            List of locations where name is defined
        """
        results = []

        for file_path, data in self.index.items():
            # Check functions
            for func in data.get('functions', []):
                if func['name'] == name:
                    results.append({
                        'file': file_path,
                        'line': func['start_line'],
                        'type': 'function'
                    })

            # Check classes
            for cls in data.get('classes', []):
                if cls['name'] == name:
                    results.append({
                        'file': file_path,
                        'line': cls['start_line'],
                        'type': 'class'
                    })

        return results

    def save_index(self, output_path: Optional[str] = None):
        """
        Save index to disk as JSON

        Args:
            output_path: Where to save (default: cache_dir/index.json)
        """
        if output_path is None:
            # Create cache directory if it doesn't exist
            os.makedirs(self.cache_dir, exist_ok=True)
            output_path = os.path.join(self.cache_dir, 'index.json')

        with open(output_path, 'w') as f:
            json.dump(self.index, f, indent=2)

        print(f"Index saved to {output_path}")

    def load_index(self, input_path: Optional[str] = None):
        """
        Load index from disk

        Args:
            input_path: Where to load from (default: cache_dir/index.json)
        """
        if input_path is None:
            input_path = os.path.join(self.cache_dir, 'index.json')

        with open(input_path, 'r') as f:
            self.index = json.load(f)

        print(f"Index loaded from {input_path}")
