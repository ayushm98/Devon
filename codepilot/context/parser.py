"""
Python Code Parser using AST
Extracts structured information from Python files
"""

import ast
import os
from typing import Dict, List, Any, Optional


class CodeParser:
    """
    Parse Python code using AST to extract structured information
    """

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a Python file and extract all structural elements

        Args:
            file_path: Path to the Python file to parse

        Returns:
            Dictionary containing:
            - file_path: str
            - language: 'python'
            - imports: List of import statements
            - functions: List of function definitions
            - classes: List of class definitions
            - globals: List of global variables
            - total_lines: int
            - parse_errors: List of error messages (empty if successful)
        """
        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            # Count total lines
            total_lines = len(source_code.split('\n'))

            # Parse the AST
            tree = ast.parse(source_code, filename=file_path)

            # Extract elements
            result = {
                'file_path': file_path,
                'language': 'python',
                'imports': self._extract_imports(tree),
                'functions': self._extract_functions(tree, source_code),
                'classes': self._extract_classes(tree, source_code),
                'globals': self._extract_globals(tree),
                'total_lines': total_lines,
                'parse_errors': []
            }

            return result

        except FileNotFoundError:
            return {
                'file_path': file_path,
                'parse_errors': [f"File not found: '{file_path}'"]
            }
        except SyntaxError as e:
            return {
                'file_path': file_path,
                'parse_errors': [f"Syntax error at line {e.lineno}: {e.msg}"]
            }
        except Exception as e:
            return {
                'file_path': file_path,
                'parse_errors': [f"Parse error: {str(e)}"]
            }

    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract all import statements"""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'name': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno,
                        'type': 'import'
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append({
                        'name': f"{module}.{alias.name}" if module else alias.name,
                        'module': module,
                        'imported': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno,
                        'type': 'from'
                    })

        return imports

    def _extract_functions(self, tree: ast.AST, source_code: str) -> List[Dict[str, Any]]:
        """Extract all function definitions"""
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Get function parameters
                params = [arg.arg for arg in node.args.args]

                # Get docstring
                docstring = ast.get_docstring(node)

                # Check if async
                is_async = isinstance(node, ast.AsyncFunctionDef)

                # Get decorators
                decorators = [ast.unparse(dec) for dec in node.decorator_list]

                functions.append({
                    'name': node.name,
                    'start_line': node.lineno,
                    'end_line': node.end_lineno,
                    'parameters': params,
                    'docstring': docstring,
                    'is_async': is_async,
                    'decorators': decorators
                })

        return functions

    def _extract_classes(self, tree: ast.AST, source_code: str) -> List[Dict[str, Any]]:
        """Extract all class definitions"""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Get base classes
                bases = [ast.unparse(base) for base in node.bases]

                # Get docstring
                docstring = ast.get_docstring(node)

                # Get methods
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append({
                            'name': item.name,
                            'is_async': isinstance(item, ast.AsyncFunctionDef),
                            'line': item.lineno
                        })

                # Get decorators
                decorators = [ast.unparse(dec) for dec in node.decorator_list]

                classes.append({
                    'name': node.name,
                    'start_line': node.lineno,
                    'end_line': node.end_lineno,
                    'bases': bases,
                    'docstring': docstring,
                    'methods': methods,
                    'decorators': decorators
                })

        return classes

    def _extract_globals(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract global variable assignments"""
        globals_list = []

        # Only look at module-level assignments
        for node in tree.body if isinstance(tree, ast.Module) else []:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Try to infer type from value
                        value_type = self._infer_type(node.value)

                        globals_list.append({
                            'name': target.id,
                            'line': node.lineno,
                            'type': value_type
                        })

        return globals_list

    def _infer_type(self, node: ast.AST) -> str:
        """Infer type from AST node"""
        if isinstance(node, ast.Constant):
            return type(node.value).__name__
        elif isinstance(node, ast.List):
            return 'list'
        elif isinstance(node, ast.Dict):
            return 'dict'
        elif isinstance(node, ast.Set):
            return 'set'
        elif isinstance(node, ast.Tuple):
            return 'tuple'
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
            return 'object'
        else:
            return 'unknown'

    def extract_code_chunk(self, file_path: str, element_name: str) -> str:
        """
        Extract a specific function or class with its dependencies

        Args:
            file_path: Path to the Python file
            element_name: Name of function or class to extract

        Returns:
            Complete code chunk including relevant imports and the element itself
        """
        try:
            # Parse the file
            result = self.parse_file(file_path)

            if result.get('parse_errors'):
                return f"Error: {result['parse_errors'][0]}"

            # Read source code
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Find the element
            element_lines = None

            # Check functions
            for func in result.get('functions', []):
                if func['name'] == element_name:
                    element_lines = (func['start_line'], func['end_line'])
                    break

            # Check classes
            if not element_lines:
                for cls in result.get('classes', []):
                    if cls['name'] == element_name:
                        element_lines = (cls['start_line'], cls['end_line'])
                        break

            if not element_lines:
                return f"Error: '{element_name}' not found in {file_path}"

            # Extract the code chunk
            start_line, end_line = element_lines
            chunk_lines = lines[start_line - 1:end_line]

            # Add relevant imports at the beginning
            import_lines = []
            for imp in result.get('imports', []):
                import_lines.append(lines[imp['line'] - 1])

            # Combine imports and element code
            if import_lines:
                code_chunk = ''.join(import_lines) + '\n' + ''.join(chunk_lines)
            else:
                code_chunk = ''.join(chunk_lines)

            return code_chunk.strip()

        except FileNotFoundError:
            return f"Error: File '{file_path}' not found."
        except Exception as e:
            return f"Error extracting code chunk: {str(e)}"

    def get_file_summary(self, file_path: str) -> str:
        """
        Generate a concise summary of file contents

        Args:
            file_path: Path to the Python file

        Returns:
            Formatted summary string
        """
        try:
            result = self.parse_file(file_path)

            if result.get('parse_errors'):
                return f"Error: {result['parse_errors'][0]}"

            # Build summary
            summary = []
            summary.append(f"File: {file_path}")
            summary.append(f"Lines: {result.get('total_lines', 0)}")

            # Functions
            functions = result.get('functions', [])
            if functions:
                func_names = ', '.join(f"{f['name']}()" for f in functions[:5])
                if len(functions) > 5:
                    func_names += f", ... ({len(functions) - 5} more)"
                summary.append(f"Functions ({len(functions)}): {func_names}")

            # Classes
            classes = result.get('classes', [])
            if classes:
                class_names = ', '.join(c['name'] for c in classes[:3])
                if len(classes) > 3:
                    class_names += f", ... ({len(classes) - 3} more)"
                summary.append(f"Classes ({len(classes)}): {class_names}")

            # Imports
            imports = result.get('imports', [])
            if imports:
                # Get unique module names
                modules = set()
                for imp in imports:
                    if imp['type'] == 'import':
                        modules.add(imp['name'].split('.')[0])
                    else:
                        modules.add(imp.get('module', '').split('.')[0] if imp.get('module') else imp['name'])

                import_list = ', '.join(sorted(modules)[:5])
                if len(modules) > 5:
                    import_list += f", ... ({len(modules) - 5} more)"
                summary.append(f"Imports: {import_list}")

            return '\n'.join(summary)

        except Exception as e:
            return f"Error generating summary: {str(e)}"
