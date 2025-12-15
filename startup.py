"""
Startup wrapper for Chainlit deployment on Render.

This script validates environment and provides better error messages
if something goes wrong during startup.
"""

import os
import sys

def check_environment():
    """Validate required environment variables."""
    required_vars = ['OPENAI_API_KEY', 'E2B_API_KEY']
    missing = []

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            # Show first/last 4 chars for verification
            masked = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            print(f"✓ {var}={masked}")

    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("\nPlease set these in your Render dashboard:")
        print("  Settings → Environment → Add Environment Variable")
        sys.exit(1)

    print("✓ All required environment variables present\n")

def check_imports():
    """Check critical imports."""
    print("Checking imports...")
    try:
        import chainlit
        print(f"✓ chainlit {chainlit.__version__}")
    except ImportError as e:
        print(f"❌ Failed to import chainlit: {e}")
        sys.exit(1)

    try:
        from codepilot.agents.orchestrator import Orchestrator
        print("✓ codepilot.agents.orchestrator")
    except ImportError as e:
        print(f"❌ Failed to import orchestrator: {e}")
        sys.exit(1)

    try:
        from codepilot.tools.context_tools import index_codebase
        print("✓ codepilot.tools.context_tools")
    except ImportError as e:
        print(f"❌ Failed to import context_tools: {e}")
        sys.exit(1)

    print("✓ All imports successful\n")

if __name__ == "__main__":
    print("=" * 50)
    print("CodePilot Startup Check")
    print("=" * 50 + "\n")

    # Check environment
    check_environment()

    # Check imports
    check_imports()

    print("=" * 50)
    print("✓ Startup checks passed!")
    print("=" * 50 + "\n")

    print("Starting Chainlit...\n")

    # Import and run chainlit
    import subprocess
    import sys

    # Get host and port from command line or environment
    port = os.getenv('PORT', '8000')
    host = '0.0.0.0'

    # Run chainlit
    cmd = [sys.executable, '-m', 'chainlit', 'run', 'chainlit_app.py',
           '--host', host, '--port', port]

    print(f"Running: {' '.join(cmd)}\n")
    subprocess.run(cmd)
