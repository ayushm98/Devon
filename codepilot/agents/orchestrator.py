"""
Orchestrator - Manages multi-agent workflow

The orchestrator is the "brain" that:
1. Tracks current state (planning, coding, reviewing, etc.)
2. Decides which agent to call next
3. Manages communication between agents
4. Handles the overall task flow
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from codepilot.agents.planner_agent import PlannerAgent
from codepilot.agents.coder_agent import CoderAgent
from codepilot.agents.reviewer_agent import ReviewerAgent


class AgentState(Enum):
    """Possible states in the multi-agent workflow"""
    PLANNING = "planning"
    CODING = "coding"
    REVIEWING = "reviewing"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class TaskContext:
    """
    Shared context passed between agents.

    Think of this as a clipboard that agents write to and read from.
    """
    task_description: str  # Original task from user
    plan: Optional[str] = None  # Created by Planner
    code_changes: Optional[Dict[str, str]] = None  # Created by Coder
    review_feedback: Optional[str] = None  # Created by Reviewer
    error_message: Optional[str] = None  # Set if something fails

    # Metadata
    current_step: int = 0
    total_steps: int = 0
    iterations: int = 0  # How many times we've looped


class Orchestrator:
    """
    Orchestrator manages the multi-agent workflow.

    Flow:
    1. Start in PLANNING state
    2. Call Planner agent → get plan
    3. Transition to CODING state
    4. Call Coder agent → get code
    5. Transition to REVIEWING state
    6. Call Reviewer agent → get feedback
    7. If approved → COMPLETE
       If rejected → back to CODING (loop)
    """

    def __init__(self, max_iterations: int = 5):
        """
        Initialize orchestrator.

        Args:
            max_iterations: Max loops between coding and reviewing
                           (prevents infinite loops if code keeps failing)
        """
        self.state = AgentState.PLANNING
        self.max_iterations = max_iterations
        self.context = None

        # Create agent instances
        self.planner = PlannerAgent()
        self.coder = CoderAgent()
        self.reviewer = ReviewerAgent()

    def run(self, task: str) -> Dict[str, Any]:
        """
        Run the multi-agent workflow for a task.

        Args:
            task: User's task description (e.g., "Add a login feature")

        Returns:
            Result dict with status, changes, and messages
        """
        # Initialize context
        self.context = TaskContext(task_description=task)
        self.state = AgentState.PLANNING

        # Main state machine loop
        while self.state not in [AgentState.COMPLETE, AgentState.FAILED]:
            # Safety: prevent infinite loops
            if self.context.iterations >= self.max_iterations:
                self.state = AgentState.FAILED
                self.context.error_message = f"Max iterations ({self.max_iterations}) exceeded"
                break

            # Execute current state
            if self.state == AgentState.PLANNING:
                self._execute_planning()

            elif self.state == AgentState.CODING:
                self._execute_coding()

            elif self.state == AgentState.REVIEWING:
                self._execute_reviewing()

            self.context.iterations += 1

        # Return final result
        return self._build_result()

    def _execute_planning(self):
        """
        Execute planning state: call Planner agent.

        Planner's job:
        - Understand the task
        - Search codebase for relevant files
        - Create step-by-step plan

        Transition: Always go to CODING next
        """
        print(f"\n[ORCHESTRATOR] State: PLANNING")
        print(f"[ORCHESTRATOR] Task: {self.context.task_description}")

        # Call the real Planner agent!
        self.context.plan = self.planner.run(self.context.task_description)

        # Transition to coding
        self.state = AgentState.CODING
        print(f"[ORCHESTRATOR] Plan created. Transitioning to CODING")

    def _execute_coding(self):
        """
        Execute coding state: call Coder agent.

        Coder's job:
        - Read the plan
        - Read relevant files
        - Write code changes

        Transition: Always go to REVIEWING next
        """
        print(f"\n[ORCHESTRATOR] State: CODING")

        # Check if this is a rework (Reviewer rejected previous code)
        if self.context.review_feedback:
            print(f"[ORCHESTRATOR] Passing plan + REVIEWER FEEDBACK to Coder agent...")
        else:
            print(f"[ORCHESTRATOR] Passing plan to Coder agent...")

        # Call the real Coder agent (with review feedback if available)!
        self.context.code_changes = self.coder.run(
            plan=self.context.plan,
            task=self.context.task_description,
            review_feedback=self.context.review_feedback
        )

        # Transition to reviewing
        self.state = AgentState.REVIEWING
        print(f"[ORCHESTRATOR] Code written. Transitioning to REVIEWING")

    def _execute_reviewing(self):
        """
        Execute reviewing state: call Reviewer agent.

        Reviewer's job:
        - Read the code changes
        - Check for bugs, style issues
        - Approve or reject

        Transition:
        - If approved → COMPLETE
        - If rejected → back to CODING (with feedback)
        """
        print(f"\n[ORCHESTRATOR] State: REVIEWING")
        print(f"[ORCHESTRATOR] Passing code changes to Reviewer agent...")

        # Call the real Reviewer agent!
        approved, feedback = self.reviewer.run(
            code_changes=self.context.code_changes,
            plan=self.context.plan,
            task=self.context.task_description
        )

        # Store the feedback
        self.context.review_feedback = feedback

        if approved:
            print(f"[ORCHESTRATOR] Code APPROVED. Transitioning to COMPLETE")
            self.state = AgentState.COMPLETE
        else:
            print(f"[ORCHESTRATOR] Code REJECTED. Transitioning back to CODING")
            self.state = AgentState.CODING

    def _build_result(self) -> Dict[str, Any]:
        """
        Build final result dictionary.

        Returns:
            Dict with status, code changes, and metadata
        """
        return {
            'status': self.state.value,
            'success': self.state == AgentState.COMPLETE,
            'task': self.context.task_description,
            'plan': self.context.plan,
            'code_changes': self.context.code_changes,
            'review_feedback': self.context.review_feedback,
            'error': self.context.error_message,
            'iterations': self.context.iterations
        }

    def get_state_history(self) -> str:
        """Get a summary of the orchestration flow."""
        return f"""
Orchestrator Summary:
- Final State: {self.state.value}
- Iterations: {self.context.iterations}
- Task: {self.context.task_description}
- Plan Created: {'Yes' if self.context.plan else 'No'}
- Code Written: {'Yes' if self.context.code_changes else 'No'}
"""
