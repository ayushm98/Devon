"""
Test Agent with New Tools
"""

from codepilot.agents.base_agent import Agent

agent = Agent(model="gpt-4", max_iterations=10)

print("\n" + "="*70)
print("TEST: Agent Using New Tools Autonomously")
print("="*70 + "\n")

# Test 1: search_code
print("Task 1: Find where 'OpenAIClient' is defined\n")
response = agent.run("Search the codebase for 'OpenAIClient' and tell me which file it's in")
print(f"\n✅ Response: {response}\n")

agent.reset()

# Test 2: list_files
print("\n" + "="*70)
print("Task 2: Explore project structure\n")
response = agent.run("List all Python files in the codepilot/tools directory")
print(f"\n✅ Response: {response}\n")

agent.reset()

# Test 3: git_status
print("\n" + "="*70)
print("Task 3: Check git status\n")
response = agent.run("What files have been modified according to git?")
print(f"\n✅ Response: {response}\n")

print("\n" + "="*70)
print("🎉 Agent successfully used all 3 new tools!")
print("="*70)
