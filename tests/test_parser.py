"""
Test the Code Parser
"""

from codepilot.context.parser import CodeParser

print("="*70)
print("TEST: Code Parser - Extracting Structured Information from Python Files")
print("="*70 + "\n")

parser = CodeParser()

# Test 1: Parse a real file from codepilot
print("Test 1: Parse codepilot/tools/file_tools.py")
print("-" * 70)

result = parser.parse_file("codepilot/tools/file_tools.py")

if result.get('parse_errors'):
    print(f"❌ Parse failed: {result['parse_errors']}")
else:
    print(f"✅ Successfully parsed {result['file_path']}")
    print(f"   Total lines: {result['total_lines']}")
    print(f"   Functions found: {len(result['functions'])}")
    print(f"   Imports found: {len(result['imports'])}")
    print(f"   Classes found: {len(result['classes'])}")
    print()

    # Show functions
    print("   Functions:")
    for func in result['functions']:
        params = ', '.join(func['parameters'])
        print(f"     - {func['name']}({params}) at lines {func['start_line']}-{func['end_line']}")
    print()

    # Show imports (first 5)
    print("   Imports (first 5):")
    for imp in result['imports'][:5]:
        if imp['type'] == 'import':
            print(f"     - import {imp['name']}")
        else:
            print(f"     - from {imp.get('module', '')} import {imp.get('imported', '')}")
    print()

# Test 2: Parse agent file (has classes)
print("\nTest 2: Parse codepilot/agents/base_agent.py")
print("-" * 70)

result = parser.parse_file("codepilot/agents/base_agent.py")

if result.get('parse_errors'):
    print(f"❌ Parse failed: {result['parse_errors']}")
else:
    print(f"✅ Successfully parsed {result['file_path']}")
    print(f"   Classes found: {len(result['classes'])}")
    print()

    # Show classes
    for cls in result['classes']:
        print(f"   Class: {cls['name']}")
        print(f"     Lines: {cls['start_line']}-{cls['end_line']}")
        print(f"     Methods: {len(cls['methods'])}")
        for method in cls['methods']:
            print(f"       - {method['name']}()")
        if cls['docstring']:
            print(f"     Docstring: {cls['docstring'][:60]}...")
        print()

# Test 3: Extract specific function
print("\nTest 3: Extract specific function (read_file)")
print("-" * 70)

chunk = parser.extract_code_chunk("codepilot/tools/file_tools.py", "read_file")

if chunk.startswith("Error"):
    print(f"❌ {chunk}")
else:
    print(f"✅ Successfully extracted 'read_file' function")
    print(f"   Code chunk length: {len(chunk)} characters")
    print(f"   First 200 characters:")
    print(f"   {chunk[:200]}...")
    print()

# Test 4: Get file summary
print("\nTest 4: Get file summary")
print("-" * 70)

summary = parser.get_file_summary("codepilot/agents/base_agent.py")
print("Summary:")
print(summary)
print()

# Test 5: Handle parsing errors gracefully
print("\nTest 5: Handle errors (non-existent file)")
print("-" * 70)

result = parser.parse_file("nonexistent_file.py")

if result.get('parse_errors'):
    print(f"✅ Correctly caught error: {result['parse_errors'][0]}")
else:
    print(f"❌ Should have failed for non-existent file")
print()

# Test 6: Parse registry file (has global variables)
print("\nTest 6: Parse registry (global variables)")
print("-" * 70)

result = parser.parse_file("codepilot/tools/registry.py")

if result.get('parse_errors'):
    print(f"❌ Parse failed: {result['parse_errors']}")
else:
    print(f"✅ Successfully parsed {result['file_path']}")
    print(f"   Global variables found: {len(result['globals'])}")
    for g in result['globals'][:5]:
        print(f"     - {g['name']} (type: {g['type']}) at line {g['line']}")
    print()

# Test 7: Get summary for multiple files
print("\nTest 7: Generate summaries for all codepilot files")
print("-" * 70)

import os

python_files = []
for root, dirs, files in os.walk("codepilot"):
    # Skip __pycache__
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for file in files:
        if file.endswith('.py'):
            python_files.append(os.path.join(root, file))

print(f"Found {len(python_files)} Python files in codepilot/\n")

for py_file in python_files:
    summary = parser.get_file_summary(py_file)
    print(summary)
    print()

print("="*70)
print("✅ All parser tests complete!")
print("="*70)
