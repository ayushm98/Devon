#!/bin/bash
set -e

echo "=================================="
echo "CodePilot Deployment Diagnostics"
echo "=================================="
echo ""

echo "1. Python version:"
python --version
echo ""

echo "2. Current directory:"
pwd
echo ""

echo "3. Directory contents:"
ls -la
echo ""

echo "4. Environment variables:"
echo "PORT=${PORT}"
echo "OPENAI_API_KEY=${OPENAI_API_KEY:0:8}...${OPENAI_API_KEY: -4}"
echo "E2B_API_KEY=${E2B_API_KEY:0:8}...${E2B_API_KEY: -4}"
echo "CHAINLIT_PASSWORD is set: $([ -n "$CHAINLIT_PASSWORD" ] && echo 'yes' || echo 'no')"
echo ""

echo "5. Testing Python imports:"
python -c "import sys; print('  ✓ sys')"
python -c "import os; print('  ✓ os')"
python -c "import chainlit; print(f'  ✓ chainlit {chainlit.__version__}')" || echo "  ✗ chainlit import failed"
python -c "from codepilot.agents.orchestrator import Orchestrator; print('  ✓ codepilot.agents.orchestrator')" || echo "  ✗ codepilot import failed"
echo ""

echo "6. Starting Chainlit..."
echo "Command: chainlit run chainlit_app.py --host 0.0.0.0 --port ${PORT}"
echo ""

# Start Chainlit
exec chainlit run chainlit_app.py --host 0.0.0.0 --port ${PORT}
