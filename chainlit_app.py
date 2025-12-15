"""
Chainlit UI for CodePilot Multi-Agent System

This provides a chat interface showing detailed agent workflow:
- Planner creates implementation plans
- Coder writes code, uploads to sandbox, runs tests
- Reviewer checks and approves code

User can see every step in real-time.
"""

import chainlit as cl
import os
import sys
import io
from contextlib import redirect_stdout, redirect_stderr
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Check if running in production BEFORE importing heavy dependencies
# Detects: Render, HuggingFace Spaces, or any cloud with PORT env var
IS_PRODUCTION = os.getenv('RENDER_SERVICE_NAME') or os.getenv('RENDER') or os.getenv('SPACE_ID') or os.getenv('PORT')

# Only import heavy ML dependencies in local development
if not IS_PRODUCTION:
    from codepilot.tools.context_tools import index_codebase

# Import orchestrator (lighter weight)
from codepilot.agents.orchestrator import Orchestrator

# Import GitHub tools for repo cloning
from codepilot.tools.github_tools import (
    extract_github_url,
    clone_repository,
    get_repo_info,
    cleanup_repository
)


# Authentication disabled for now - uncomment to enable password protection
# @cl.password_auth_callback
# def auth_callback(username: str, password: str):
#     """
#     Simple password authentication for CodePilot.
#
#     For production, use environment variables and proper password hashing.
#     """
#     # Get password from environment variable (more secure)
#     required_password = os.getenv('CHAINLIT_PASSWORD', 'codepilot2024')
#
#     # In production, you should hash passwords and use a proper auth system
#     if password == required_password:
#         return cl.User(
#             identifier=username,
#             metadata={"role": "user", "provider": "credentials"}
#         )
#     return None


@cl.on_chat_start
async def start():
    """Initialize the agent system when chat starts."""

    print("[CHAINLIT] on_chat_start triggered")  # Debug log

    await cl.Message(
        content="# CodePilot - Autonomous AI Coding Agent\n\n"
                "I can help you write code, fix bugs, and implement features!\n\n"
                "**How to use:**\n"
                "1. Paste a **public GitHub URL** and I'll clone and analyze it\n"
                "2. Tell me what you want to build or fix\n"
                "3. Watch my agents (Planner > Coder > Reviewer) work!\n\n"
                "**Example:**\n"
                "```\nAnalyze https://github.com/user/repo and add error handling to the API endpoints\n```\n\n"
                "**Ready!** Paste a GitHub URL or describe your task."
    ).send()

    print("[CHAINLIT] Welcome message sent")  # Debug log

    # Initialize session variables
    cl.user_session.set("repo_path", None)
    cl.user_session.set("repo_info", None)

    # Skip indexing on deployment to avoid startup issues (using module-level constant)
    if IS_PRODUCTION:
        print(f"[CHAINLIT] Running in production mode (PORT={os.getenv('PORT')}) - skipping codebase indexing")
        cl.user_session.set("orchestrator", Orchestrator(max_iterations=3))
        cl.user_session.set("ready", True)
        print("[CHAINLIT] Orchestrator created, ready=True")
        return

    # Index codebase in background (only in local development)
    index_msg = await cl.Message(content="Indexing codebase...").send()

    try:
        # Get project root
        project_root = os.path.dirname(os.path.abspath(__file__))
        index_result = index_codebase(project_root)

        # Update message content
        index_msg.content = f"Codebase indexed!\n```\n{index_result}\n```"
        await index_msg.update()

        # Store orchestrator in session (reduced iterations to save API credits)
        cl.user_session.set("orchestrator", Orchestrator(max_iterations=3))
        cl.user_session.set("ready", True)

    except Exception as e:
        # Update message content
        index_msg.content = f"Indexing failed (will continue anyway):\n```\n{str(e)}\n```"
        await index_msg.update()
        # Still create orchestrator even if indexing fails
        cl.user_session.set("orchestrator", Orchestrator(max_iterations=10))
        cl.user_session.set("ready", True)


@cl.on_chat_end
async def end():
    """Cleanup when chat ends."""
    # Clean up any cloned repositories
    repo_path = cl.user_session.get("repo_path")
    if repo_path:
        print(f"[CHAINLIT] Cleaning up repo: {repo_path}")
        cleanup_repository(repo_path)


@cl.on_message
async def main(message: cl.Message):
    """Handle user messages and run the agent workflow."""

    # Check if ready
    if not cl.user_session.get("ready"):
        await cl.Message(content="System is still initializing, please wait...").send()
        return

    # Get orchestrator
    orchestrator: Orchestrator = cl.user_session.get("orchestrator")

    # Check for GitHub URL in message
    github_url = extract_github_url(message.content)
    task_context = ""

    if github_url:
        # Clone the repository
        clone_msg = await cl.Message(content=f"Cloning repository: `{github_url}`...").send()

        success, result, repo_name = clone_repository(github_url)

        if success:
            repo_path = result
            repo_info = get_repo_info(repo_path)

            # Store in session
            cl.user_session.set("repo_path", repo_path)
            cl.user_session.set("repo_info", repo_info)

            # Create context for the task (limited to avoid token overflow)
            languages = ", ".join(repo_info["languages"][:5]) if repo_info["languages"] else "Unknown"
            # Only include first 20 files to keep context small
            sample_files = repo_info["files"][:20] if repo_info["files"] else []
            files_preview = "\n".join(f"  - {f}" for f in sample_files)
            if len(repo_info["files"]) > 20:
                files_preview += f"\n  ... and {len(repo_info['files']) - 20} more files"

            task_context = f"""
[REPOSITORY CONTEXT]
Repository: {repo_name}
Path: {repo_path}
Total Files: {repo_info['total_files']}
Languages: {languages}
Sample Files:
{files_preview}

IMPORTANT: Use the read_file tool with the full path (e.g., {repo_path}/filename.py) to read files.
"""
            # Update clone message
            clone_msg.content = f"**Repository cloned successfully!**\n\n" \
                               f"- **Name:** {repo_name}\n" \
                               f"- **Files:** {repo_info['total_files']}\n" \
                               f"- **Languages:** {languages}\n" \
                               f"- **Path:** `{repo_path}`"
            await clone_msg.update()

        else:
            # Clone failed
            clone_msg.content = f"**Failed to clone repository**\n\n{result}\n\n" \
                               f"Make sure the repository is public and the URL is correct."
            await clone_msg.update()
            return

    # Check if we have a repo from previous message
    elif cl.user_session.get("repo_path"):
        repo_path = cl.user_session.get("repo_path")
        repo_info = cl.user_session.get("repo_info")
        if repo_info:
            languages = ", ".join(repo_info["languages"][:5]) if repo_info["languages"] else "Unknown"
            task_context = f"""
[REPOSITORY CONTEXT]
Repository: {repo_info['name']}
Path: {repo_path}
Total Files: {repo_info['total_files']}
Languages: {languages}

IMPORTANT: Use the read_file tool with the full path (e.g., {repo_path}/filename.py) to read files.
"""

    # Prepare the full task with context
    full_task = task_context + message.content if task_context else message.content

    # Create a message for streaming logs
    log_msg = cl.Message(content="")
    await log_msg.send()

    try:
        # Capture stdout/stderr to stream logs
        captured_output = io.StringIO()

        def run_orchestrator():
            """Run orchestrator in thread and capture output."""
            try:
                with redirect_stdout(captured_output), redirect_stderr(captured_output):
                    return orchestrator.run(full_task)
            except Exception as e:
                # Capture any exceptions from orchestrator
                print(f"Error in orchestrator: {str(e)}")
                import traceback
                traceback.print_exc()
                raise

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)

        # Start the orchestrator in background
        future = loop.run_in_executor(executor, run_orchestrator)

        # Track API usage
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0
        seen_token_lines = set()  # Track which token lines we've already counted

        # Stream logs while orchestrator is running - FILTERED
        accumulated_logs = ""
        while not future.done():
            await asyncio.sleep(0.5)  # Check every 500ms

            # Get new output
            current_output = captured_output.getvalue()
            if current_output != accumulated_logs:
                accumulated_logs = current_output

                # Filter logs to show only important lines
                filtered_lines = []
                for line in accumulated_logs.split('\n'):
                    # Extract token usage before filtering (only count each line once!)
                    if 'Tokens:' in line and line not in seen_token_lines:
                        seen_token_lines.add(line)  # Mark as counted
                        try:
                            # Parse: "Tokens: 505 prompt + 20 completion = 525 total"
                            parts = line.split('Tokens:')[1].strip()
                            prompt = int(parts.split('prompt')[0].strip())
                            completion = int(parts.split('+')[1].split('completion')[0].strip())
                            total_prompt_tokens += prompt
                            total_completion_tokens += completion
                            total_tokens += (prompt + completion)
                        except:
                            pass

                    # Skip token counts, progress bars, and verbose details
                    if any(skip in line for skip in ['Tokens:', 'Batches:', '|##', 'it/s]']):
                        continue
                    # Keep important lines
                    if any(keep in line for keep in [
                        '[ORCHESTRATOR]', '[PLANNER]', '[CODER]', '[REVIEWER]',
                        'Calling tool:', 'Tool', 'Transitioning', 'APPROVED', 'REJECTED',
                        '[GITHUB]', 'Cloning', 'Repository'
                    ]):
                        filtered_lines.append(line)

                filtered_output = '\n'.join(filtered_lines)

                # Calculate cost (GPT-3.5-turbo pricing: $0.0015/1K input, $0.002/1K output)
                input_cost = (total_prompt_tokens / 1000) * 0.0015
                output_cost = (total_completion_tokens / 1000) * 0.002
                total_cost = input_cost + output_cost

                # Add usage summary to logs
                usage_summary = f"\n\nCREDITS USED:\n"
                usage_summary += f"  Input:  {total_prompt_tokens:,} tokens (${input_cost:.4f})\n"
                usage_summary += f"  Output: {total_completion_tokens:,} tokens (${output_cost:.4f})\n"
                usage_summary += f"  Total:  {total_tokens:,} tokens (${total_cost:.4f})"

                # Update message with filtered logs + usage
                log_msg.content = f"```\n{filtered_output}\n{usage_summary}\n```"
                await log_msg.update()

        # Get final result
        result = await future

        # Get final logs
        final_logs = captured_output.getvalue()

        # Update with final logs
        log_msg.content = f"## Execution Log\n```\n{final_logs}\n```"
        await log_msg.update()

        # Send results summary
        summary_lines = []

        if result.get('plan'):
            summary_lines.append("## Planner")
            summary_lines.append(f"Plan created ({len(result['plan'])} chars)\n")

        if result.get('code_changes'):
            summary_lines.append("## Coder")
            summary_lines.append(f"Created {len(result['code_changes'])} file(s):")
            for file_path in result['code_changes'].keys():
                summary_lines.append(f"  - {file_path}")
            summary_lines.append("")

        if result.get('review_feedback'):
            summary_lines.append("## Reviewer")
            if result.get('success'):
                summary_lines.append("Code approved")
            else:
                summary_lines.append("Needs revision")
            summary_lines.append("")

        summary_lines.append("## Result")
        if result.get('success'):
            summary_lines.append(f"**Success** (Iterations: {result.get('iterations', 'N/A')})")
        else:
            summary_lines.append(f"**Incomplete** (Iterations: {result.get('iterations', 'N/A')})")

        # Add final cost summary
        summary_lines.append("\n## API Credits Used (GPT-3.5-Turbo)")
        summary_lines.append(f"**Total Tokens:** {total_tokens:,}")
        summary_lines.append(f"- Input: {total_prompt_tokens:,} tokens (${(total_prompt_tokens/1000)*0.0015:.4f})")
        summary_lines.append(f"- Output: {total_completion_tokens:,} tokens (${(total_completion_tokens/1000)*0.002:.4f})")
        summary_lines.append(f"\n**Estimated Cost:** ${total_cost:.4f}")

        await cl.Message(content="\n".join(summary_lines)).send()

    except Exception as e:
        # Determine error type and provide specific guidance
        error_message = str(e)
        error_type = type(e).__name__

        if "rate_limit" in error_message.lower() or "429" in error_message:
            user_message = f"""## Rate Limit Reached

OpenAI API rate limit exceeded. This happens when too many requests are made in a short time.

**What to do:**
- Wait a few minutes and try again
- Reduce max_iterations (currently: {orchestrator.max_iterations})
- Your request will work once the rate limit resets

**Error details:**
```
{error_message}
```
"""
        elif "insufficient_quota" in error_message.lower():
            user_message = f"""## API Credits Exhausted

Your OpenAI API credits have been exhausted.

**What to do:**
- Add credits to your OpenAI account at https://platform.openai.com/account/billing
- Check your usage at https://platform.openai.com/usage
- Current model: GPT-3.5-turbo (~$0.02 per task)

**Error details:**
```
{error_message}
```
"""
        elif "api_key" in error_message.lower() or "authentication" in error_message.lower():
            user_message = f"""## API Key Error

There's an issue with your OpenAI API key.

**What to do:**
- Verify your OPENAI_API_KEY in .env file
- Check that the key is valid at https://platform.openai.com/api-keys
- Restart the application after updating .env

**Error details:**
```
{error_message}
```
"""
        elif "timeout" in error_message.lower():
            user_message = f"""## Request Timeout

The operation took too long and timed out.

**What to do:**
- Try again with a simpler task
- The task may be too complex for one iteration
- Consider breaking it into smaller steps

**Error details:**
```
{error_message}
```
"""
        else:
            # Generic error with helpful context
            user_message = f"""## Error Occurred

An unexpected error occurred during execution.

**Error type:** {error_type}

**What to do:**
- Try rephrasing your request
- Check if all required files/dependencies exist
- Verify your .env file has all required API keys

**Error details:**
```
{error_message}
```

If this persists, please report the issue with the error details above.
"""

        await cl.Message(content=user_message).send()


if __name__ == "__main__":
    import sys
    sys.exit("Run with: chainlit run chainlit_app.py")
