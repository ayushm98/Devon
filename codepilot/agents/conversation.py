"""
Conversation Manager
Handles conversation history in OpenAI's message format
"""

from typing import List, Dict, Any


class ConversationManager:
    """Manages conversation history for the agent"""

    def __init__(self):
        """Initialize with empty message history"""
        self.messages: List[Dict[str, Any]] = []

    def add_user_message(self, content: str):
        """
        Add a user message to the conversation

        Args:
            content: The user's message text
        """
        self.messages.append({
            "role": "user",
            "content": content
        })
        print(f"👤 User: {content[:100]}..." if len(content) > 100 else f"👤 User: {content}")

    def add_assistant_message(self, content: str):
        """
        Add an assistant text response to the conversation

        Args:
            content: The assistant's response text
        """
        self.messages.append({
            "role": "assistant",
            "content": content
        })
        print(f"🤖 Assistant: {content[:100]}..." if len(content) > 100 else f"🤖 Assistant: {content}")

    def add_assistant_tool_calls(self, tool_calls: List[Any]):
        """
        Add an assistant message with tool calls

        Args:
            tool_calls: List of tool call objects from OpenAI response
        """
        # Extract tool call info for logging
        tool_names = [tc.function.name for tc in tool_calls]
        print(f"🔧 Assistant calling tools: {tool_names}")

        # OpenAI requires this specific format
        self.messages.append({
            "role": "assistant",
            "content": None,  # No text content when making tool calls
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in tool_calls
            ]
        })

    def add_tool_result(self, tool_call_id: str, tool_name: str, result: str):
        """
        Add a tool execution result to the conversation

        Args:
            tool_call_id: The ID of the tool call (from OpenAI)
            tool_name: Name of the tool that was executed
            result: The result string from the tool
        """
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": result
        })
        # Truncate long results for logging
        result_preview = result[:100] + "..." if len(result) > 100 else result
        print(f"✅ Tool {tool_name} result: {result_preview}")

    def get_messages(self) -> List[Dict[str, Any]]:
        """
        Get the full conversation history

        Returns:
            List of message dictionaries
        """
        return self.messages

    def clear(self):
        """Clear all messages from history"""
        self.messages = []
        print("🗑️  Conversation cleared")

    def get_message_count(self) -> int:
        """
        Get the number of messages in the conversation

        Returns:
            Number of messages
        """
        return len(self.messages)

    def print_summary(self):
        """Print a summary of the conversation"""
        print(f"\n📊 Conversation Summary:")
        print(f"  Total messages: {len(self.messages)}")

        role_counts = {}
        for msg in self.messages:
            role = msg.get("role", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1

        for role, count in role_counts.items():
            print(f"  {role}: {count}")
