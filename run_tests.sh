#!/bin/bash
# Run all tests

source venv/bin/activate

echo "Running all tests..."
echo ""

echo "=== Test 1: OpenAI Connection ==="
python -m tests.test_openai_connection
echo ""

echo "=== Test 2: LLM Client ==="
python -m tests.test_llm_client
echo ""

echo "=== Test 3: Tools Registry ==="
python -m tests.test_tools
echo ""

echo "=== Test 4: Conversation Manager ==="
python -m tests.test_conversation
echo ""

echo "=== Test 5: Full Agent ==="
python -m tests.test_agent
echo ""

echo "✅ All tests completed!"
