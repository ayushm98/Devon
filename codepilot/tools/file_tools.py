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
