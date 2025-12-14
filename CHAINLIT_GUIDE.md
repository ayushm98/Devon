# Chainlit UI Guide

## Quick Start

### 1. Make sure dependencies are installed
```bash
source venv/bin/activate
pip install chainlit
```

### 2. Run the Chainlit app
```bash
chainlit run chainlit_app.py
```

### 3. Open your browser
Chainlit will automatically open `http://localhost:8000`

## What You'll See

### Welcome Screen
- Introduction to CodePilot
- Explanation of the 3-agent workflow
- Codebase indexing status

### During Task Execution
You'll see detailed real-time updates:

```
📋 Task Received
-------------------
Your task description here

🤔 PLANNER: Searching codebase...
🤔 PLANNER: ✅ Plan created

📝 Implementation Plan
-------------------
Detailed plan appears here

💻 CODER: Writing code...
💻 CODER: ✅ Code written locally

💻 Code Written
-------------------
📄 fibonacci.py
📄 test_fibonacci.py

📤 CODER: Uploading to sandbox...
🧪 CODER: Running tests in sandbox...
✅ CODER: Tests passed in sandbox!

👁️ REVIEWER: Checking code quality...
✅ REVIEWER: Code approved!

🎯 Workflow Complete
-------------------
✅ Status: Success
- ✅ Planner created implementation plan
- ✅ Coder wrote 2 file(s)
- ✅ Code tested in isolated sandbox
- ✅ Reviewer approved changes

Iterations: 3

📊 Detailed Workflow:
START → planning → coding → reviewing → complete
```

## Example Tasks

Try these commands in the chat:

1. **Simple function:**
   ```
   Create a function to calculate factorial of a number with tests
   ```

2. **Bug fix:**
   ```
   Fix any bugs in fibonacci.py and add input validation
   ```

3. **Feature addition:**
   ```
   Add a function to calculate the first N fibonacci numbers and return as a list
   ```

## Features

### Real-Time Progress
- See each agent's actions as they happen
- Watch code being written, uploaded, and tested
- View test results instantly

### Code Preview
- See the code that was written
- Preview files before they're saved
- Review test outputs

### Workflow Transparency
- Full state history showing agent transitions
- Iteration count
- Success/failure status

## Troubleshooting

### "Connection refused"
Make sure you ran `chainlit run chainlit_app.py` not `python chainlit_app.py`

### "Module not found: chainlit"
Run `pip install chainlit` in your activated venv

### Indexing fails
The app will still work! Indexing is optional for better context.

### Sandbox not showing tests
Check that E2B_API_KEY is set in your .env file

## Architecture

The UI connects to:
```
Chainlit UI (Port 8000)
    ↓
Orchestrator
    ↓
├── PlannerAgent (searches codebase, creates plan)
├── CoderAgent (writes code, tests in sandbox)
└── ReviewerAgent (checks code quality)
    ↓
E2B Sandbox (isolated code execution)
```

## Next Steps

After the workflow completes:
1. Check the files that were created
2. Review the code in your editor
3. Run tests locally if desired
4. Commit to git when satisfied

## Configuration

Edit `chainlit_app.py` to customize:
- `max_iterations=10` - Maximum workflow iterations
- Message formatting and emojis
- Status update frequency
- Code preview length (currently 500 chars)
