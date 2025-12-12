"""
Tool Registry
Maps tool names to their implementations and schemas
"""

from codepilot.tools.file_tools import read_file, write_file, run_command
from typing import Callable, List, Dict, Optional


# Tool schemas for OpenAI function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads the contents of a file at the specified path. Use this when you need to view or analyze file contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to read (absolute or relative path)"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Writes content to a file at the specified path. Creates the file if it doesn't exist, overwrites if it does. Use this when you need to create or modify files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to write to (absolute or relative path)"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Executes a shell command in the system terminal. Use this for running scripts, installing packages, or executing system commands.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute"
                    }
                },
                "required": ["command"]
            }
        }
    }
]


# Map tool names to their implementation functions
TOOL_FUNCTIONS = {
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command
}


def get_tools() -> List[Dict]:
    """
    Get all available tool schemas

    Returns:
        List of tool schema dictionaries for OpenAI
    """
    return TOOLS


def get_tool_function(tool_name: str) -> Optional[Callable]:
    """
    Get the implementation function for a tool by name

    Args:
        tool_name: Name of the tool (e.g., "read_file")

    Returns:
        The tool function, or None if not found
    """
    return TOOL_FUNCTIONS.get(tool_name)


def list_tool_names() -> List[str]:
    """
    Get list of all available tool names

    Returns:
        List of tool name strings
    """
    return list(TOOL_FUNCTIONS.keys())
