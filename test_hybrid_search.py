"""
Test script for Hybrid Retrieval System
"""

from codepilot.tools.context_tools import index_codebase, search_codebase

print("=" * 60)
print("Testing Hybrid Retrieval System")
print("=" * 60)

# Step 1: Index the codebase
print("\n[1] Indexing codebase...")
result = index_codebase("/Users/ayush/devon")
print(result)

# Step 2: Test some searches
queries = [
    "agent loop",
    "file operations",
    "error handling"
]

for query in queries:
    print(f"\n{'=' * 60}")
    print(f"[SEARCH] Query: '{query}'")
    print("=" * 60)
    results = search_codebase(query, top_k=3)
    print(results)

print("\n" + "=" * 60)
print("Testing complete!")
print("=" * 60)
