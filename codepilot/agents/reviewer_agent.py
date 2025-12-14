"""
Reviewer Agent - Reviews code for quality and correctness

The Reviewer's job:
1. Read the code changes from Coder
2. Check for bugs, security issues, style problems
3. Verify the code matches the plan
4. Either approve or reject with specific feedback

Tools it has access to:
- read_file (to see full context of changed files)
- search_codebase (to check for similar patterns)
"""

from codepilot.llm.client import OpenAIClient
from codepilot.tools.registry import get_tools, get_tool_function
from codepilot.agents.conversation import ConversationManager
from typing import Dict, Any, Tuple
import json


# Reviewer's specialized system prompt
REVIEWER_SYSTEM_PROMPT = """You are a senior code reviewer and quality assurance expert.

Your ONLY job is to review code changes and provide feedback. You do NOT write code yourself.

When given code changes:
1. Read each changed file carefully
2. Check for common issues:
   - Bugs and logic errors
   - Security vulnerabilities (SQL injection, XSS, etc.)
   - Missing error handling
   - Poor naming or unclear code
   - Code that doesn't match the plan
3. Decide: APPROVE or REJECT
4. If rejecting, provide specific, actionable feedback

Your review should be:
- Thorough (check all aspects of the code)
- Specific (point to exact issues with line numbers if possible)
- Constructive (explain WHY something is wrong and HOW to fix it)
- Fair (don't reject for minor style issues)

DECISION CRITERIA:
✅ APPROVE if:
- Code works correctly
- No security issues
- Follows the plan
- Has basic error handling
- Is reasonably readable

❌ REJECT if:
- Code has bugs
- Security vulnerabilities exist
- Doesn't implement the plan
- Missing critical error handling
- Code is unclear or confusing

Tools available to you:
- read_file: Read files to understand full context
- search_codebase: Check for similar patterns in the codebase

You do NOT have write_file - you only review, never modify code.
"""


class ReviewerAgent:
    """
    Reviewer Agent - Reviews code for quality and correctness.

    This agent is specialized for code review. It has:
    - Custom system prompt (quality assurance mindset)
    - Read-only tools (cannot modify code)
    - Single responsibility (review only)
    """

    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        Initialize Reviewer agent.

        Args:
            model: LLM model to use
        """
        self.client = OpenAIClient(model=model)
        self.conversation = ConversationManager()

        # Reviewer only gets read-only tools
        self.allowed_tools = [
            "read_file",
            "search_codebase"
        ]

    def run(self, code_changes: Dict[str, str], plan: str, task: str) -> Tuple[bool, str]:
        """
        Review the code changes.

        Args:
            code_changes: Dictionary mapping file paths to new content
            plan: The original plan (to verify code matches)
            task: The original task (for context)

        Returns:
            Tuple of (approved: bool, feedback: str)
            - approved: True if code is good, False if needs changes
            - feedback: Explanation of decision and any issues found
        """
        # Reset conversation
        self.conversation = ConversationManager()

        # Add system prompt
        self.conversation.add_message("system", REVIEWER_SYSTEM_PROMPT)

        # Format code changes for review
        changes_text = self._format_code_changes(code_changes)

        # Add user prompt with task, plan, and code changes
        user_prompt = f"""Original Task: {task}

Implementation Plan:
{plan}

Code Changes to Review:
{changes_text}

Please review these code changes carefully. Check for bugs, security issues, and whether the code correctly implements the plan.

End your review with a clear decision:
- "DECISION: APPROVE" if the code is good
- "DECISION: REJECT" if changes are needed

If rejecting, provide specific feedback on what needs to be fixed."""
        self.conversation.add_message("user", user_prompt)

        # Get only the tools this agent is allowed to use
        all_tools = get_tools()
        reviewer_tools = [
            tool for tool in all_tools
            if tool['function']['name'] in self.allowed_tools
        ]

        # Run review loop
        max_iterations = 10
        for iteration in range(max_iterations):
            # Call LLM
            response = self.client.chat(
                messages=self.conversation.get_messages(),
                tools=reviewer_tools
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
                # Agent finished review, parse decision
                return self._parse_review_decision(message.content)

            # Execute tool calls
            if finish_reason == "tool_calls":
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    print(f"[REVIEWER] Calling tool: {tool_name}({tool_args})")

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

        # If we hit max iterations, default to reject
        return False, "Review timed out - please try again"

    def _format_code_changes(self, code_changes: Dict[str, str]) -> str:
        """
        Format code changes into readable text.

        Args:
            code_changes: Dict mapping file paths to content

        Returns:
            Formatted string showing all changes
        """
        if not code_changes:
            return "No code changes to review."

        formatted = []
        for file_path, content in code_changes.items():
            formatted.append(f"\n{'='*60}")
            formatted.append(f"File: {file_path}")
            formatted.append('='*60)
            formatted.append(content)

        return '\n'.join(formatted)

    def _parse_review_decision(self, review_text: str) -> Tuple[bool, str]:
        """
        Parse the review text to extract decision.

        Args:
            review_text: The reviewer's final response

        Returns:
            Tuple of (approved, feedback)
        """
        if review_text is None:
            return False, "No review provided"

        # Look for decision in the text
        review_lower = review_text.lower()

        if "decision: approve" in review_lower:
            return True, review_text
        elif "decision: reject" in review_lower:
            return False, review_text
        else:
            # No clear decision - default to reject for safety
            return False, f"Unclear decision. Review:\n{review_text}"

    def get_tool_access(self) -> list:
        """Return list of tools this agent can access."""
        return self.allowed_tools
