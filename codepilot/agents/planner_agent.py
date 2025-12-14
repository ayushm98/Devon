"""
Planner Agent - Creates implementation plans

The Planner's job:
1. Understand the task
2. Search the codebase to see what exists
3. Create a detailed, step-by-step plan

Tools it has access to:
- search_codebase (hybrid retrieval)
- read_file (to understand existing code)
- list_files (to explore structure)
"""

from codepilot.llm.client import OpenAIClient
from codepilot.tools.registry import get_tools, get_tool_function
from codepilot.agents.conversation import ConversationManager
from typing import Dict, Any
import json


# Planner's specialized system prompt
PLANNER_SYSTEM_PROMPT = """You are a senior software architect and planning expert.

Your ONLY job is to create detailed implementation plans. You do NOT write code.

When given a task:
1. First, search the codebase to understand what already exists
2. Identify which files need to be modified or created
3. Break down the task into clear, specific steps
4. Consider dependencies and potential risks

Your plan should be:
- Specific (mention exact file names, function names)
- Ordered (steps build on each other)
- Complete (covers all aspects of the task)
- Realistic (considers existing code structure)

Output your plan as a numbered list of steps.

Tools available to you:
- search_codebase: Search for existing code (use this first!)
- read_file: Read specific files to understand them
- list_files: Explore directory structure

You do NOT have write_file or run_command - you only plan, never execute.
"""


class PlannerAgent:
    """
    Planner Agent - Creates implementation plans.

    This agent is specialized for planning. It has:
    - Custom system prompt (architect mindset)
    - Limited tools (read-only)
    - Single responsibility (planning only)
    """

    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        Initialize Planner agent.

        Args:
            model: LLM model to use
        """
        self.client = OpenAIClient(model=model)
        self.conversation = ConversationManager()

        # Planner only gets read-only tools
        self.allowed_tools = [
            "search_codebase",
            "read_file",
            "list_files"
        ]

    def run(self, task: str) -> str:
        """
        Create a plan for the given task.

        Args:
            task: Task description (e.g., "Add login feature")

        Returns:
            Detailed implementation plan as a string
        """
        # Reset conversation
        self.conversation = ConversationManager()

        # Add system prompt
        self.conversation.add_message("system", PLANNER_SYSTEM_PROMPT)

        # Add user task
        user_prompt = f"""Task: {task}

Please create a detailed implementation plan. Start by searching the codebase to understand what exists."""
        self.conversation.add_message("user", user_prompt)

        # Get only the tools this agent is allowed to use
        all_tools = get_tools()
        planner_tools = [
            tool for tool in all_tools
            if tool['function']['name'] in self.allowed_tools
        ]

        # Run planning loop (agent explores codebase, then creates plan)
        max_iterations = 10
        for iteration in range(max_iterations):
            # Call LLM
            response = self.client.chat(
                messages=self.conversation.get_messages(),
                tools=planner_tools
            )

            finish_reason = response.choices[0].finish_reason
            message = response.choices[0].message

            # Add assistant response to conversation
            self.conversation.add_message(
                role="assistant",
                content=message.content,
                tool_calls=message.tool_calls
            )

            # Check if done
            if finish_reason == "stop":
                # Agent finished planning
                return message.content

            # Execute tool calls
            if finish_reason == "tool_calls":
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    print(f"[PLANNER] Calling tool: {tool_name}({tool_args})")

                    # Execute tool
                    tool_func = get_tool_function(tool_name)
                    if tool_func:
                        result = tool_func(**tool_args)
                    else:
                        result = f"Error: Tool {tool_name} not found"

                    # Add tool result to conversation
                    self.conversation.add_tool_result(
                        tool_call_id=tool_call.id,
                        tool_name=tool_name,
                        result=str(result)
                    )

        # If we hit max iterations, return what we have
        return "Error: Planner exceeded max iterations"

    def get_tool_access(self) -> list:
        """Return list of tools this agent can access."""
        return self.allowed_tools
