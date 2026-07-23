from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from state import AgentState
from agents.coordinator import coordinator_node
from agents.routing import route_next_step
from agents.appointment import appointment_node
from agents.intake import intake_node
from tools.appointments import book_appointment, fetch_available_slots, cancel_appointment
from tools.patients import register_patient

# --- Build the Graph ---
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("coordinator", coordinator_node)
workflow.add_node("appointment_agent", appointment_node)
workflow.add_node("intake_agent", intake_node)
workflow.add_node("tools", ToolNode([book_appointment, fetch_available_slots, cancel_appointment, register_patient]))

# Set the entry point
workflow.set_entry_point("coordinator")

# Add Conditional Edges from the Coordinator
# FIXED: Added intake_agent to the routing map
workflow.add_conditional_edges(
    "coordinator",
    route_next_step,
    {
        "appointment_agent": "appointment_agent",
        "intake_agent": "intake_agent",
        "end": END
    }
)

def route_tool_return(state: dict):
    """Routes the graph back to the agent that called the tool."""
    current_task = state.get("current_task")
    
    if current_task == "intake_agent":
        return "intake_agent"
    elif current_task == "appointment_agent":
        return "appointment_agent"
    
    # Fallback just in case
    return "appointment_agent"

# Define the Agent-Tool Loop
# tools_condition automatically checks if the LLM output contains 'tool_calls'. 
# If it does, it routes to "tools". If it doesn't, it routes to END.

# Route from agents TO the tools
workflow.add_conditional_edges(
    "intake_agent",
    tools_condition,
    {"tools": "tools", "__end__": END}
)

workflow.add_conditional_edges(
    "appointment_agent",
    tools_condition,
    {"tools": "tools", "__end__": END}
)

# Route from tools BACK to the correct agent
workflow.add_conditional_edges(
    "tools",
    route_tool_return
)

# FIXED: Deleted the two static add_edge("tools", ...) lines from here.

# Add a Memory Saver to the Graph
memory = MemorySaver()

# Compile the Graph
app_graph = workflow.compile(checkpointer=memory)