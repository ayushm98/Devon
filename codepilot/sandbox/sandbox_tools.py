"""
Sandbox Tools for AI Agents

These tools allow agents to safely execute code in isolated environments.
"""

from codepilot.sandbox.e2b_sandbox import E2BSandboxManager
from typing import Dict, Any

# Global sandbox instance (shared across tool calls)
_sandbox_manager: E2BSandboxManager = None


def create_sandbox() -> str:
    """
    Create a new E2B sandbox for code execution.

    Returns:
        Success message with sandbox ID
    """
    global _sandbox_manager

    try:
        _sandbox_manager = E2BSandboxManager()
        return _sandbox_manager.create()
    except Exception as e:
        return f"❌ Failed to create sandbox: {str(e)}"


def close_sandbox() -> str:
    """
    Close and destroy the current sandbox.

    Returns:
        Success message
    """
    global _sandbox_manager

    if _sandbox_manager is None:
        return "No sandbox to close"

    result = _sandbox_manager.close()
    _sandbox_manager = None
    return result


def upload_to_sandbox(path: str, content: str) -> str:
    """
    Upload a file to the sandbox.

    Args:
        path: Path where file should be written in sandbox (e.g., "test.py")
        content: File content to upload

    Returns:
        Success or error message
    """
    global _sandbox_manager

    if _sandbox_manager is None or not _sandbox_manager.is_running():
        # Auto-create sandbox if it doesn't exist
        create_result = create_sandbox()
        if "❌" in create_result:
            return create_result

    return _sandbox_manager.upload_file(path, content)


def execute_in_sandbox(code: str) -> str:
    """
    Execute Python code in the sandbox.

    Args:
        code: Python code to execute

    Returns:
        Formatted output with stdout and stderr
    """
    global _sandbox_manager

    if _sandbox_manager is None or not _sandbox_manager.is_running():
        # Auto-create sandbox if it doesn't exist
        create_result = create_sandbox()
        if "❌" in create_result:
            return create_result

    result = _sandbox_manager.run_code(code)

    # Format the output nicely
    output = []
    if result["stdout"]:
        output.append(f"📤 Output:\n{result['stdout']}")
    if result["stderr"]:
        output.append(f"⚠️  Errors:\n{result['stderr']}")
    if result.get("error"):
        output.append(f"❌ Error: {result['error']}")

    return "\n\n".join(output) if output else "✅ Code executed successfully (no output)"


def run_command_in_sandbox(command: str) -> str:
    """
    Run a shell command in the sandbox.

    Args:
        command: Shell command to execute (e.g., "python test.py", "pytest")

    Returns:
        Command output
    """
    global _sandbox_manager

    if _sandbox_manager is None or not _sandbox_manager.is_running():
        # Auto-create sandbox if it doesn't exist
        create_result = create_sandbox()
        if "❌" in create_result:
            return create_result

    result = _sandbox_manager.run_command(command)

    # Format the output
    output = []
    if result["stdout"]:
        output.append(f"📤 Output:\n{result['stdout']}")
    if result["stderr"]:
        output.append(f"⚠️  Errors:\n{result['stderr']}")
    if result["exit_code"] != 0:
        output.append(f"❌ Exit code: {result['exit_code']}")

    return "\n\n".join(output) if output else "✅ Command executed successfully (no output)"


def list_sandbox_files(path: str = ".") -> str:
    """
    List files in the sandbox directory.

    Args:
        path: Directory path to list (default: current directory)

    Returns:
        List of files
    """
    global _sandbox_manager

    if _sandbox_manager is None or not _sandbox_manager.is_running():
        return "❌ No sandbox running. Create one first."

    return _sandbox_manager.list_files(path)


def read_sandbox_file(path: str) -> str:
    """
    Read a file from the sandbox.

    Args:
        path: File path in sandbox

    Returns:
        File contents
    """
    global _sandbox_manager

    if _sandbox_manager is None or not _sandbox_manager.is_running():
        return "❌ No sandbox running. Create one first."

    return _sandbox_manager.read_file(path)


# Helper function to get current sandbox status
def get_sandbox_status() -> str:
    """
    Get the current sandbox status.

    Returns:
        Status message
    """
    global _sandbox_manager

    if _sandbox_manager is None:
        return "No sandbox created"
    elif _sandbox_manager.is_running():
        return f"✅ Sandbox running (ID: {_sandbox_manager.sandbox.id})"
    else:
        return "Sandbox closed"
