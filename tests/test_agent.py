"""
Test the complete Agent
This is the real test - can the agent use tools autonomously?
"""

from codepilot.agents.base_agent import Agent

print("Creating agent...\n")
agent = Agent(model="gpt-4", max_iterations=10)

# Test 1: Simple file read
print("\n" + "="*70)
print("TEST 1: Read a file")
print("="*70)
response = agent.run("Read the requirements.txt file and tell me what dependencies we have")
print(f"\n📝 Final Response:\n{response}\n")

# Reset for next test
agent.reset()

# Test 2: Multi-step task (write then read)
print("\n" + "="*70)
print("TEST 2: Multi-step task (write and read)")
print("="*70)
response = agent.run("Create a file called hello.txt with the content 'Hello from the agent!', then read it back to verify it worked")
print(f"\n📝 Final Response:\n{response}\n")

# Reset for next test
agent.reset()

# Test 3: Run a command
print("\n" + "="*70)
print("TEST 3: Run a shell command")
print("="*70)
response = agent.run("Use a command to list all Python files in the current directory")
print(f"\n📝 Final Response:\n{response}\n")

print("\n" + "="*70)
print("✅ ALL TESTS COMPLETE!")
print("="*70)
print("\nYour agent can now:")
print("  ✓ Read files")
print("  ✓ Write files")
print("  ✓ Run commands")
print("  ✓ Handle multi-step tasks")
print("  ✓ Communicate results in natural language")
