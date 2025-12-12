"""
Test the OpenAI Client wrapper
"""

from codepilot.llm.client import OpenAIClient

# Test 1: Simple chat without tools
print("=== Test 1: Simple Chat ===")
client = OpenAIClient(model="gpt-4")

messages = [
    {"role": "user", "content": "Say 'Hello from the client wrapper!' in exactly those words."}
]

response = client.chat(messages=messages)
print(f"Response: {response.choices[0].message.content}\n")

# Test 2: Chat with tools (even though we won't use them yet)
print("=== Test 2: Chat with Tools Available ===")

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }
]

messages = [
    {"role": "user", "content": "Just say hello, don't use any tools."}
]

response = client.chat(messages=messages, tools=tools)
print(f"Response: {response.choices[0].message.content}")
print(f"Finish reason: {response.choices[0].finish_reason}")

print("\n✅ Client wrapper is working!")
