"""
Test the Conversation Manager
"""

from codepilot.agents.conversation import ConversationManager

# Create a conversation manager
conv = ConversationManager()

print("=== Test 1: Add user message ===")
conv.add_user_message("Read the file app.py")
print()

print("=== Test 2: Add assistant message ===")
conv.add_assistant_message("I'll read that file for you.")
print()

print("=== Test 3: Simulate tool call ===")
# Simulate what OpenAI returns
class MockToolCall:
    def __init__(self):
        self.id = "call_123"
        self.function = type('obj', (object,), {
            'name': 'read_file',
            'arguments': '{"path": "app.py"}'
        })()

tool_calls = [MockToolCall()]
conv.add_assistant_tool_calls(tool_calls)
print()

print("=== Test 4: Add tool result ===")
conv.add_tool_result(
    tool_call_id="call_123",
    tool_name="read_file",
    result="Successfully read file 'app.py':\n\nimport os\n..."
)
print()

print("=== Test 5: Add final assistant response ===")
conv.add_assistant_message("The file app.py contains tool definitions.")
print()

print("=== Test 6: Get conversation history ===")
messages = conv.get_messages()
print(f"Total messages: {len(messages)}")
for i, msg in enumerate(messages, 1):
    role = msg.get("role")
    print(f"  {i}. {role}")
print()

print("=== Test 7: Print summary ===")
conv.print_summary()
print()

print("✅ Conversation Manager working!")
