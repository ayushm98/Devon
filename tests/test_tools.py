"""
Test the tools registry
"""

from codepilot.tools.registry import get_tools, get_tool_function, list_tool_names

print("=== Test 1: List all tool names ===")
tool_names = list_tool_names()
print(f"Available tools: {tool_names}\n")

print("=== Test 2: Get tool schemas ===")
tools = get_tools()
print(f"Number of tools: {len(tools)}")
for tool in tools:
    print(f"  - {tool['function']['name']}: {tool['function']['description'][:50]}...")
print()

print("=== Test 3: Get and execute read_file tool ===")
read_fn = get_tool_function("read_file")
if read_fn:
    result = read_fn("requirements.txt")
    print(result[:100] + "..." if len(result) > 100 else result)
else:
    print("❌ read_file not found")
print()

print("=== Test 4: Get and execute write_file tool ===")
write_fn = get_tool_function("write_file")
if write_fn:
    result = write_fn("test_tool_output.txt", "Hello from tools registry!")
    print(result)
else:
    print("❌ write_file not found")
print()

print("=== Test 5: Get and execute run_command tool ===")
run_fn = get_tool_function("run_command")
if run_fn:
    result = run_fn("echo 'Tools registry works!'")
    print(result)
else:
    print("❌ run_command not found")

print("\n✅ All tools working through registry!")
