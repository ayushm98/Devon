"""
OpenAI Client Wrapper
Handles all communication with OpenAI's API
"""

import os
from dotenv import load_dotenv
import openai
from typing import List, Dict, Optional

load_dotenv()


class OpenAIClient:
    """Wrapper for OpenAI API calls"""

    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        Initialize OpenAI client

        Args:
            model: OpenAI model to use (default: gpt-3.5-turbo)
        """
        self.api_key = os.getenv('OPENAI_API_KEY')

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = model

        print(f"✅ OpenAI Client initialized with model: {self.model}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> openai.types.chat.ChatCompletion:
        """
        Send a chat completion request to OpenAI

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions for function calling
            temperature: Randomness (0-2, lower = more focused)
            max_tokens: Maximum tokens in response

        Returns:
            OpenAI ChatCompletion response object
        """
        try:
            # Build request parameters
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            # Add tools if provided
            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = "auto"

            # Make API call
            response = self.client.chat.completions.create(**request_params)

            # Print token usage for cost tracking
            usage = response.usage
            print(f"📊 Tokens: {usage.prompt_tokens} prompt + {usage.completion_tokens} completion = {usage.total_tokens} total")

            return response

        except openai.APIError as e:
            print(f"❌ OpenAI API Error: {e}")
            raise
        except openai.RateLimitError as e:
            print(f"❌ Rate Limit Error: {e}")
            raise
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            raise
