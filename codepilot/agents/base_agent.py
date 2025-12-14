"""
Base Agent
The main agent loop that orchestrates LLM calls and tool execution
"""

import json
from codepilot.llm.client import OpenAIClient
from codepilot.agents.conversation import ConversationManager
from codepilot.tools.registry import get_tools, get_tool_function


class Agent:
    """Main agent that executes tasks using LLM and tools"""

    def __init__(self, model: str = "gpt-3.5-turbo", max_iterations: int = 10):
        """
        Initialize the agent

        Args:
            model: OpenAI model to use
            max_iterations: Maximum number of LLM calls to prevent infinite loops
        """
        print("🚀 Initializing Agent...")

        # Initialize components
        self.client = OpenAIClient(model=model)
        self.conversation = ConversationManager()
        self.tools = get_tools()
        self.max_iterations = max_iterations

        print(f"✅ Agent ready with {len(self.tools)} tools")
        print(f"   Max iterations: {max_iterations}\n")

    def run(self, user_prompt: str) -> str:
        """
        Run the agent with a user prompt

        Args:
            user_prompt: The user's request

        Returns:
            Final response from the agent
        """
        print("=" * 60)
        print("🤖 AGENT STARTING")
        print("=" * 60)

        # Add user message to conversation
        self.conversation.add_user_message(user_prompt)

        # Main agent loop
        for iteration in range(1, self.max_iterations + 1):
            print(f"\n--- Iteration {iteration}/{self.max_iterations} ---")

            # Call OpenAI with current conversation and tools
            response = self.client.chat(
                messages=self.conversation.get_messages(),
                tools=self.tools
            )

            # Get the assistant's response
            message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            print(f"🎯 Finish reason: {finish_reason}")

            # Check what the assistant wants to do
            if finish_reason == "stop":
                # Assistant is done, has a text response
                final_response = message.content
                self.conversation.add_assistant_message(final_response)

                print("\n" + "=" * 60)
                print("✅ AGENT COMPLETE")
                print("=" * 60)

                return final_response

            elif finish_reason == "tool_calls":
                # Assistant wants to use tools
                tool_calls = message.tool_calls

                # Add the assistant's tool calls to conversation
                self.conversation.add_assistant_tool_calls(tool_calls)

                # Execute each tool call
                for tool_call in tool_calls:
                    self._execute_tool_call(tool_call)

                # Continue loop - send results back to OpenAI
                continue

            else:
                # Unexpected finish reason
                error_msg = f"Unexpected finish_reason: {finish_reason}"
                print(f"⚠️  {error_msg}")
                return error_msg

        # Max iterations reached
        max_iter_msg = f"⚠️  Reached maximum iterations ({self.max_iterations})"
        print(f"\n{max_iter_msg}")
        return max_iter_msg

    def _execute_tool_call(self, tool_call):
        """
        Execute a single tool call

        Args:
            tool_call: Tool call object from OpenAI response
        """
        tool_id = tool_call.id
        tool_name = tool_call.function.name
        tool_args_json = tool_call.function.arguments

        print(f"\n🔧 Executing tool: {tool_name}")
        print(f"   ID: {tool_id}")
        print(f"   Arguments: {tool_args_json}")

        try:
            # Parse arguments from JSON string
            tool_args = json.loads(tool_args_json)

            # Get the tool function
            tool_function = get_tool_function(tool_name)

            if tool_function is None:
                result = f"Error: Tool '{tool_name}' not found in registry"
                print(f"❌ {result}")
            else:
                # Execute the tool
                result = tool_function(**tool_args)

            # Add result to conversation
            self.conversation.add_tool_result(
                tool_call_id=tool_id,
                tool_name=tool_name,
                result=result
            )

        except json.JSONDecodeError as e:
            error_msg = f"Error parsing tool arguments: {e}"
            print(f"❌ {error_msg}")
            self.conversation.add_tool_result(
                tool_call_id=tool_id,
                tool_name=tool_name,
                result=error_msg
            )

        except Exception as e:
            error_msg = f"Error executing tool: {str(e)}"
            print(f"❌ {error_msg}")
            self.conversation.add_tool_result(
                tool_call_id=tool_id,
                tool_name=tool_name,
                result=error_msg
            )

    def reset(self):
        """Reset the agent's conversation history"""
        self.conversation.clear()
        print("🔄 Agent conversation reset")
