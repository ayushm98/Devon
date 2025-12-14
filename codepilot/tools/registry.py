"""
Tool Registry
Maps tool names to their implementations and schemas
"""

from codepilot.tools.file_tools import read_file, write_file, run_command, search_code, list_files, git_status
from codepilot.tools.context_tools import search_codebase, index_codebase
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
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Search for a text pattern in code files (like grep). Use this to find where functions, classes, or text appears in the codebase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "The text pattern to search for"
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory to search in (default: current directory)"
                    },
                    "file_extension": {
                        "type": "string",
                        "description": "Optional file extension filter (e.g., 'py', 'js')"
                    }
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories in a path. Use this to explore the project structure or find files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path to list (default: current directory)"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Optional glob pattern to filter files (e.g., '*.py', 'test_*')"
                    },
                    "show_hidden": {
                        "type": "boolean",
                        "description": "Whether to show hidden files (default: false)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "Get the git repository status. Use this to see what files have been modified, added, or deleted.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_codebase",
            "description": "Search the codebase using hybrid retrieval (combines keyword matching with semantic search). More powerful than search_code - finds both exact matches AND semantically related code. Use this when looking for specific functionality, patterns, or concepts in the codebase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for. Can be natural language (e.g., 'authentication logic', 'error handling') or specific terms (e.g., 'login function', 'database connection')"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5, max: 20)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    }
]


# Map tool names to their implementation functions
TOOL_FUNCTIONS = {
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
    "search_code": search_code,
    "list_files": list_files,
    "git_status": git_status,
    "search_codebase": search_codebase,
    "index_codebase": index_codebase
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
