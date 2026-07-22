from langgraph.graph import StateGraph, END
from state import AgentState
from agents.coordinator import coordinator_node

# --- Placeholder Nodes for the the specified agents ---
def appointment_node(state: AgentState):
    print("--- EXEC: Appointment Agent ---")
    return state

def document_node(state: AgentState):
    print("--- EXEC: Document Agent ---")
    return state

def safety_node(state: AgentState):
    print("--- EXEC: Safety Agent ---")
    return state

def followup_node(state: AgentState):
    print("--- EXEC: Followup Agent ---")
    return state

# --- Conditional Routing Logic ---
def routing_next_node(state: AgentState) -> str:
    """Reads the Coordinator's decision and tells LangGraph where to go."""
    destination = state.get("current_task", "end")
    print(f"--- ROUTING TO: {destination} ---")
    return destination

# --- Build the Graph ---
workflow = StateGraph(AgentState)

# 1. Add Nodes
workflow.add_node("coordinator", coordinator_node)
workflow.add_node("appointment_agent", appointment_node)
workflow.add_node("document_agent", document_node)
workflow.add_node("safety_agent", safety_node)
workflow.add_node("followup_agent", followup_node)

# 2. Set the entry point
workflow.set_entry_point("coordinator")

# 3. Add Conditional Edges from the Coordinator
workflow.add_conditional_edges(
    "coordinator",
    routing_next_node,
    {
        "appointment_agent": "appointment_agent",
        "document_agent": "document_agent",
        "safety_agent": "safety_agent",
        "followup_agent": "followup_agent",
        "end": END
    }
)

# 4. For now, route all specified agents back to END to finish the loop
workflow.add_edge("appointment_agent", END)
workflow.add_edge("document_agent", END)
workflow.add_edge("safety_agent", END)
workflow.add_edge("followup_agent", END)

# 5. Compile the Graph
app_graph = workflow.compile()