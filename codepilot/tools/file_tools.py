"""
File operation tools for the agent
"""

import subprocess
import os


def read_file(path):
    """
    Reads and returns the contents of a file.

    Args:
        path: File path to read

    Returns:
        str: File contents or error message
    """
    try:
        with open(path, 'r') as f:
            content = f.read()
        return f"Successfully read file '{path}':\n\n{content}"
    except FileNotFoundError:
        return f"Error: File '{path}' not found."
    except PermissionError:
        return f"Error: Permission denied to read file '{path}'."
    except Exception as e:
        return f"Error reading file '{path}': {str(e)}"


def write_file(path, content):
    """
    Writes content to a file, creating it if it doesn't exist.

    Args:
        path: File path to write to
        content: Content to write

    Returns:
        str: Success or error message
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        with open(path, 'w') as f:
            f.write(content)

        return f"Successfully wrote {len(content)} characters to '{path}'."
    except PermissionError:
        return f"Error: Permission denied to write to '{path}'."
    except Exception as e:
        return f"Error writing to file '{path}': {str(e)}"


def run_command(command):
    """
    Executes a shell command and returns the output.

    Args:
        command: Shell command to execute

    Returns:
        str: Command output or error message
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        output = []
        if result.stdout:
            output.append(f"Output:\n{result.stdout}")
        if result.stderr:
            output.append(f"Errors:\n{result.stderr}")

        status = "succeeded" if result.returncode == 0 else f"failed (exit code {result.returncode})"
        output.insert(0, f"Command '{command}' {status}.")

        return "\n\n".join(output)

    except subprocess.TimeoutExpired:
        return f"Error: Command '{command}' timed out after 30 seconds."
    except Exception as e:
        return f"Error executing command '{command}': {str(e)}"


def search_code(pattern, path=".", file_extension=None):
    """
    Search for a pattern in code files (like grep).

    Args:
        pattern: Text pattern to search for
        path: Directory to search in (default: current directory)
        file_extension: Optional file extension filter (e.g., "py", "js")

    Returns:
        str: Search results or error message
    """
    try:
        # Build grep command
        cmd_parts = ["grep", "-r", "-n", "-i", pattern, path]

        # Add file extension filter if specified
        if file_extension:
            # Remove leading dot if present
            ext = file_extension.lstrip('.')
            cmd_parts.extend(["--include", f"*.{ext}"])

        # Exclude common directories
        cmd_parts.extend([
            "--exclude-dir=venv",
            "--exclude-dir=node_modules",
            "--exclude-dir=__pycache__",
            "--exclude-dir=.git"
        ])

        result = subprocess.run(
            cmd_parts,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            # Limit results to prevent overwhelming output
            if len(lines) > 50:
                return f"Found {len(lines)} matches (showing first 50):\n\n" + '\n'.join(lines[:50])
            else:
                return f"Found {len(lines)} matches:\n\n{result.stdout}"
        elif result.returncode == 1:
            return f"No matches found for pattern '{pattern}' in {path}"
        else:
            return f"Error searching: {result.stderr}"

    except subprocess.TimeoutExpired:
        return f"Error: Search timed out after 10 seconds."
    except Exception as e:
        return f"Error searching for pattern '{pattern}': {str(e)}"


def list_files(path=".", pattern=None, show_hidden=False):
    """
    List files and directories.

    Args:
        path: Directory path to list (default: current directory)
        pattern: Optional glob pattern to filter (e.g., "*.py", "test_*")
        show_hidden: Whether to show hidden files (default: False)

    Returns:
        str: List of files or error message
    """
    try:
        import glob

        # Build the search pattern
        if pattern:
            search_path = os.path.join(path, pattern)
        else:
            search_path = os.path.join(path, "*")

        # Get all matches
        matches = glob.glob(search_path)

        # Filter hidden files if needed
        if not show_hidden:
            matches = [m for m in matches if not os.path.basename(m).startswith('.')]

        if not matches:
            return f"No files found in '{path}'" + (f" matching '{pattern}'" if pattern else "")

        # Separate files and directories
        files = []
        dirs = []

        for item in sorted(matches):
            rel_path = os.path.relpath(item, path)
            if os.path.isdir(item):
                dirs.append(f"📁 {rel_path}/")
            else:
                size = os.path.getsize(item)
                files.append(f"📄 {rel_path} ({size} bytes)")

        result = []
        result.append(f"Contents of '{path}':")
        if pattern:
            result.append(f"(filtered by: {pattern})")
        result.append("")

        if dirs:
            result.append("Directories:")
            result.extend(dirs)
            result.append("")

        if files:
            result.append("Files:")
            result.extend(files)

        result.append(f"\nTotal: {len(dirs)} directories, {len(files)} files")

        return "\n".join(result)

    except Exception as e:
        return f"Error listing files in '{path}': {str(e)}"


def git_status():
    """
    Get git repository status.

    Returns:
        str: Git status output or error message
    """
    try:
        # Check if we're in a git repo
        check_result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if check_result.returncode != 0:
            return "Not a git repository"

        # Get status
        result = subprocess.run(
            ["git", "status", "--short", "--branch"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            if result.stdout.strip():
                return f"Git Status:\n\n{result.stdout}"
            else:
                return "Git Status: Working tree clean (no changes)"
        else:
            return f"Error getting git status: {result.stderr}"

    except subprocess.TimeoutExpired:
        return "Error: Git command timed out"
    except FileNotFoundError:
        return "Error: Git is not installed"
    except Exception as e:
        return f"Error checking git status: {str(e)}"
