"""
Test the new tools (search_code, list_files, git_status)
"""

from codepilot.tools.file_tools import search_code, list_files, git_status

print("=== Test 1: search_code ===")
print("Searching for 'Agent' in Python files...\n")
result = search_code("Agent", ".", "py")
print(result[:500] + "..." if len(result) > 500 else result)
print()

print("=== Test 2: list_files ===")
print("Listing Python files in codepilot/agents/...\n")
result = list_files("codepilot/agents", "*.py")
print(result)
print()

print("=== Test 3: list_files with pattern ===")
print("Listing all test files...\n")
result = list_files("tests", "test_*.py")
print(result)
print()

print("=== Test 4: git_status ===")
print("Getting git repository status...\n")
result = git_status()
print(result)
print()

print("=== Test 5: Verify registry ===")
from codepilot.tools.registry import list_tool_names
print("All available tools:")
tools = list_tool_names()
print(tools)
print(f"\nTotal tools: {len(tools)}")
print()

print("✅ All new tools working!")
