from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from state import AgentState
from agents.coordinator import coordinator_node
from agents.routing import route_next_step
from agents.appointment import appointment_node
from tools.appointments import book_appointment, fetch_available_slots, cancel_appointment

# --- Build the Graph ---
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("coordinator", coordinator_node)
workflow.add_node("appointment_agent", appointment_node)

# Set the entry point
workflow.add_node("tools", ToolNode([book_appointment, fetch_available_slots, cancel_appointment]))

# Add Conditional Edges from the Coordinator
workflow.set_entry_point("coordinator")
workflow.add_conditional_edges(
    "coordinator",
    route_next_step,
    {
        "appointment_agent": "appointment_agent",
        "end": END
    }
)

# Define the Agent-Tool Loop
# tools_condition automatically checks if the LLM output contains 'tool_calls'. 
# If it does, it routes to "tools". If it doesn't, it routes to END.
workflow.add_conditional_edges(
    "appointment_agent",
    tools_condition,
)

# For now, route all specified agents back to END to finish the loop
workflow.add_edge("tools", "appointment_agent")

# Add a Memory Saver to the Graph
memory = MemorySaver()

# Compile the Graph
app_graph = workflow.compile(checkpointer=memory)