"""
E2B Sandbox Manager

Manages lifecycle of E2B sandboxes for safe code execution.
"""

from e2b_code_interpreter.code_interpreter_sync import Sandbox
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class E2BSandboxManager:
    """
    Manages E2B sandbox instances for isolated code execution.

    The sandbox provides:
    - Isolated filesystem (files don't affect host)
    - Safe execution (code can't access host system)
    - Clean environment (starts fresh each time)
    """

    def __init__(self):
        """
        Initialize sandbox manager.

        E2B API key is read from E2B_API_KEY environment variable.
        """
        if not os.getenv("E2B_API_KEY"):
            raise ValueError("E2B_API_KEY not found in environment variables")

        self.sandbox: Optional[Sandbox] = None
        self._is_open = False

    def create(self) -> str:
        """
        Create a new sandbox instance.

        Returns:
            Sandbox ID
        """
        if self._is_open:
            return f"Sandbox already running (ID: {self.sandbox.sandbox_id})"

        try:
            api_key = os.getenv("E2B_API_KEY")
            self.sandbox = Sandbox.create(api_key=api_key)
            self._is_open = True
            return f"✅ Sandbox created (ID: {self.sandbox.sandbox_id})"
        except Exception as e:
            return f"❌ Error creating sandbox: {str(e)}"

    def close(self) -> str:
        """
        Close and destroy the sandbox.

        Returns:
            Success message
        """
        if not self._is_open:
            return "No sandbox to close"

        try:
            if self.sandbox:
                self.sandbox.kill()
            self._is_open = False
            return "✅ Sandbox closed"
        except Exception as e:
            return f"❌ Error closing sandbox: {str(e)}"

    def upload_file(self, path: str, content: str) -> str:
        """
        Upload a file to the sandbox.

        Args:
            path: Path in sandbox where file should be written
            content: File content

        Returns:
            Success or error message
        """
        if not self._is_open:
            return "❌ No sandbox running. Create one first."

        try:
            self.sandbox.files.write(path, content)
            return f"✅ Uploaded file to sandbox: {path} ({len(content)} chars)"
        except Exception as e:
            return f"❌ Error uploading file: {str(e)}"

    def run_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Execute code in the sandbox.

        Args:
            code: Code to execute
            language: Programming language (default: python)

        Returns:
            Dict with stdout, stderr, exit_code, and error (if any)
        """
        if not self._is_open:
            return {
                "stdout": "",
                "stderr": "❌ No sandbox running. Create one first.",
                "exit_code": 1,
                "error": "No sandbox"
            }

        try:
            # Execute code in sandbox
            execution = self.sandbox.run_code(code)

            return {
                "stdout": execution.text or "",
                "stderr": execution.error or "",
                "exit_code": 0 if not execution.error else 1,
                "error": None
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
                "error": str(e)
            }

    def run_command(self, command: str) -> Dict[str, Any]:
        """
        Run a shell command in the sandbox.

        Args:
            command: Shell command to execute

        Returns:
            Dict with stdout, stderr, exit_code
        """
        if not self._is_open:
            return {
                "stdout": "",
                "stderr": "❌ No sandbox running. Create one first.",
                "exit_code": 1
            }

        try:
            # Run shell command
            process = self.sandbox.commands.run(command)

            return {
                "stdout": process.stdout,
                "stderr": process.stderr,
                "exit_code": process.exit_code
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1
            }

    def list_files(self, path: str = ".") -> str:
        """
        List files in sandbox directory.

        Args:
            path: Directory path to list

        Returns:
            List of files as string
        """
        if not self._is_open:
            return "❌ No sandbox running. Create one first."

        try:
            result = self.sandbox.commands.run(f"ls -la {path}")
            return result.stdout
        except Exception as e:
            return f"❌ Error listing files: {str(e)}"

    def read_file(self, path: str) -> str:
        """
        Read a file from the sandbox.

        Args:
            path: File path in sandbox

        Returns:
            File contents or error message
        """
        if not self._is_open:
            return "❌ No sandbox running. Create one first."

        try:
            content = self.sandbox.files.read(path)
            return content
        except Exception as e:
            return f"❌ Error reading file: {str(e)}"

    def is_running(self) -> bool:
        """Check if sandbox is currently running."""
        return self._is_open

    def __enter__(self):
        """Context manager support: with E2BSandboxManager() as sandbox:"""
        self.create()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support: automatically close on exit"""
        self.close()
