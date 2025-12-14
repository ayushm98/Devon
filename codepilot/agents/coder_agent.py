"""
Coder Agent - Implements code based on plans

The Coder's job:
1. Read the plan from Planner
2. Search/read existing code to understand it
3. Write code changes to implement the plan
4. Follow best practices and coding standards

Tools it has access to:
- search_codebase (find relevant files)
- read_file (understand existing code)
- write_file (implement changes)
- list_files (explore structure)
"""

from codepilot.llm.client import OpenAIClient
from codepilot.tools.registry import get_tools, get_tool_function
from codepilot.agents.conversation import ConversationManager
from typing import Dict, Any
import json


# Coder's specialized system prompt
CODER_SYSTEM_PROMPT = """You are an expert software engineer and implementation specialist.

Your ONLY job is to write code that implements the given plan. You do NOT create plans yourself.

When given a plan:
1. Read and understand each step carefully
2. Search the codebase to find relevant files
3. Read existing files to understand the current implementation
4. Write clean, well-structured code that follows the plan
5. Make incremental changes, one step at a time

Your code should be:
- Clean and readable (follow existing code style)
- Well-tested (add error handling)
- Documented (add comments for complex logic)
- Minimal (only change what's necessary)

IMPORTANT RULES:
- Follow the plan exactly - don't add extra features
- Match the existing code style in each file
- Test your changes mentally before writing
- If you need clarification on the plan, state what's unclear

Tools available to you:
- search_codebase: Find existing code
- read_file: Understand current implementation
- write_file: Create or modify files
- list_files: Explore directory structure
- upload_to_sandbox: Upload files to isolated testing environment
- run_command_in_sandbox: Run commands safely in sandbox (e.g., pytest, python test.py)
- execute_in_sandbox: Execute Python code snippets for quick testing

IMPORTANT: Always test your code in the sandbox before submitting!
1. Write the file locally (write_file)
2. Upload to sandbox (upload_to_sandbox)
3. Run tests in sandbox (run_command_in_sandbox)
4. Fix any issues before marking as complete
"""


class CoderAgent:
    """
    Coder Agent - Implements code based on plans.

    This agent is specialized for coding. It has:
    - Custom system prompt (engineer mindset)
    - Write access tools (can modify files)
    - Single responsibility (implementation only)
    """

    def __init__(self, model: str = "gpt-4"):
        """
        Initialize Coder agent.

        Args:
            model: LLM model to use
        """
        self.client = OpenAIClient(model=model)
        self.conversation = ConversationManager()

        # Coder gets read + write tools + sandbox execution (safe testing)
        self.allowed_tools = [
            "search_codebase",
            "read_file",
            "write_file",
            "list_files",
            "upload_to_sandbox",
            "run_command_in_sandbox",
            "execute_in_sandbox"
        ]

    def run(self, plan: str, task: str, review_feedback: str = None) -> Dict[str, str]:
        """
        Implement the given plan.

        Args:
            plan: Implementation plan from Planner
            task: Original task description (for context)
            review_feedback: Optional feedback from Reviewer if code was rejected

        Returns:
            Dictionary mapping file paths to their new content
        """
        # Reset conversation
        self.conversation = ConversationManager()

        # Add system prompt
        self.conversation.add_message("system", CODER_SYSTEM_PROMPT)

        # Build user prompt with task, plan, and optionally review feedback
        user_prompt = f"""Original Task: {task}

Implementation Plan:
{plan}"""

        # If this is a rework (Reviewer rejected the code), include feedback
        if review_feedback:
            user_prompt += f"""

IMPORTANT - REVIEWER FEEDBACK (CODE WAS REJECTED):
{review_feedback}

Please fix the issues mentioned by the Reviewer and resubmit the code."""
        else:
            user_prompt += """

Please implement this plan step by step. Write clean, well-structured code that follows the plan."""

        self.conversation.add_message("user", user_prompt)

        # Get only the tools this agent is allowed to use
        all_tools = get_tools()
        coder_tools = [
            tool for tool in all_tools
            if tool['function']['name'] in self.allowed_tools
        ]

        # Track which files were modified
        modified_files = {}

        # Run coding loop (agent reads code, writes changes)
        max_iterations = 15  # Coder might need more iterations than planner
        for iteration in range(max_iterations):
            # Call LLM
            response = self.client.chat(
                messages=self.conversation.get_messages(),
                tools=coder_tools
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
                # Agent finished coding
                print(f"[CODER] Finished implementation")
                return modified_files

            # Execute tool calls
            if finish_reason == "tool_calls":
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    print(f"[CODER] Calling tool: {tool_name}({tool_args})")

                    # Execute tool
                    tool_func = get_tool_function(tool_name)
                    if tool_func:
                        result = tool_func(**tool_args)

                        # Track file modifications
                        if tool_name == "write_file" and "path" in tool_args:
                            modified_files[tool_args["path"]] = tool_args.get("content", "")
                    else:
                        result = f"Error: Tool {tool_name} not found"

                    # Add tool result to conversation
                    self.conversation.add_tool_result(
                        tool_call_id=tool_call.id,
                        tool_name=tool_name,
                        result=str(result)
                    )

        # If we hit max iterations, return what we have
        print(f"[CODER] Warning: Hit max iterations ({max_iterations})")
        return modified_files

    def get_tool_access(self) -> list:
        """Return list of tools this agent can access."""
        return self.allowed_tools
