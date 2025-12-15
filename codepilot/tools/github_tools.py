"""
GitHub Repository Tools
Handles cloning and managing public GitHub repositories for CodePilot sessions
"""

import os
import re
import shutil
import subprocess
import tempfile
from typing import Optional, Tuple
import uuid


def extract_github_url(text: str) -> Optional[str]:
    """
    Extract a GitHub repository URL from text.

    Supports formats:
    - https://github.com/user/repo
    - https://github.com/user/repo.git
    - github.com/user/repo
    - http://github.com/user/repo

    Returns:
        GitHub URL if found, None otherwise
    """
    # Pattern to match GitHub URLs
    pattern = r'(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)(?:\.git)?'
    match = re.search(pattern, text)

    if match:
        user = match.group(1)
        repo = match.group(2).rstrip('.git')
        return f"https://github.com/{user}/{repo}.git"

    return None


def get_repo_name(github_url: str) -> str:
    """Extract repository name from GitHub URL."""
    # Remove .git suffix if present
    url = github_url.rstrip('.git')
    # Get the last part of the URL
    return url.split('/')[-1]


def clone_repository(github_url: str, base_dir: Optional[str] = None) -> Tuple[bool, str, str]:
    """
    Clone a public GitHub repository to a temporary directory.

    Args:
        github_url: The GitHub repository URL
        base_dir: Optional base directory for cloning (default: system temp)

    Returns:
        Tuple of (success: bool, path_or_error: str, repo_name: str)
    """
    repo_name = get_repo_name(github_url)

    # Create a unique session directory
    session_id = str(uuid.uuid4())[:8]

    if base_dir is None:
        # Use /tmp for cloud environments (more space than tempfile default)
        base_dir = "/tmp/codepilot_repos"

    # Ensure base directory exists
    os.makedirs(base_dir, exist_ok=True)

    # Create session-specific directory
    session_dir = os.path.join(base_dir, f"{repo_name}_{session_id}")

    try:
        # Clone with depth=1 for faster cloning (only latest commit)
        result = subprocess.run(
            ["git", "clone", "--depth", "1", github_url, session_dir],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        if result.returncode != 0:
            error_msg = result.stderr or "Unknown error during clone"
            # Clean up failed clone
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir, ignore_errors=True)
            return False, f"Clone failed: {error_msg}", repo_name

        return True, session_dir, repo_name

    except subprocess.TimeoutExpired:
        # Clean up on timeout
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir, ignore_errors=True)
        return False, "Clone timed out (repository may be too large)", repo_name

    except Exception as e:
        # Clean up on any error
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir, ignore_errors=True)
        return False, f"Clone error: {str(e)}", repo_name


def cleanup_repository(repo_path: str) -> bool:
    """
    Clean up a cloned repository.

    Args:
        repo_path: Path to the cloned repository

    Returns:
        True if cleanup successful, False otherwise
    """
    try:
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
        return True
    except Exception:
        return False


def get_repo_info(repo_path: str) -> dict:
    """
    Get basic information about a cloned repository.

    Args:
        repo_path: Path to the cloned repository

    Returns:
        Dictionary with repo info
    """
    info = {
        "path": repo_path,
        "name": os.path.basename(repo_path).split('_')[0],  # Remove session ID
        "files": [],
        "total_files": 0,
        "languages": set()
    }

    # File extension to language mapping
    ext_to_lang = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript',
        '.jsx': 'JavaScript',
        '.java': 'Java',
        '.go': 'Go',
        '.rs': 'Rust',
        '.cpp': 'C++',
        '.c': 'C',
        '.h': 'C/C++',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.cs': 'C#',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.md': 'Markdown',
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
    }

    # Walk the repository
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden directories and common non-code directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__', 'dist', 'build']]

        for file in files:
            if not file.startswith('.'):
                info["total_files"] += 1
                ext = os.path.splitext(file)[1].lower()
                if ext in ext_to_lang:
                    info["languages"].add(ext_to_lang[ext])

                # Store relative path
                rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                info["files"].append(rel_path)

    info["languages"] = list(info["languages"])

    return info


def validate_github_url(url: str) -> Tuple[bool, str]:
    """
    Validate that a URL is a valid public GitHub repository.

    Args:
        url: The URL to validate

    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    if not url:
        return False, "No URL provided"

    # Check if it's a GitHub URL
    if 'github.com' not in url.lower():
        return False, "Not a GitHub URL"

    # Extract and validate format
    extracted = extract_github_url(url)
    if not extracted:
        return False, "Invalid GitHub URL format. Expected: github.com/user/repo"

    return True, extracted
