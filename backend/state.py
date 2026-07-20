from typing import Annotated, TypedDict, List, Dict, Any, Optional
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    The shared state object for the AgentCare multi-agent workflow.
    """
    # Messages list uses LangChain's add_messages reducer to append history
    messages: Annotated[list, add_messages]
    
    # Tracks user demographic and session data
    user_context: Dict[str, Any]
    
    # Identifies the active administrative goal (e.g., "schedule_appointment", "verify_insurance")
    current_task: Optional[str]
    
    # Tracks the progress status of the current task
    task_status: str # Options: "pending", "in_progress", "awaiting_input", "complete", "error"
    
    # Stores structured output data gathered during the workflow (e.g., appointment times, document IDs)
    workflow_data: Dict[str, Any]

