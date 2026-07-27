from agents.safety import safety_node
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from state import AgentState
from agents.coordinator import coordinator_node
from agents.routing import routing_node
from agents.appointment import appointment_node
from agents.document import document_node
from agents.intake import intake_node
from tools.appointments import book_appointment, fetch_available_slots, cancel_appointment, reschedule_appointment, list_patient_appointments
from tools.documents import classify_and_store_document, extract_document_metadata, update_patient_record, audit_required_forms
from tools.patients import register_patient

print(f"{'='*50}")
print("--- Graph Initialization ---")
print(f"{'='*50}")

# --- Build the Graph ---
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("safety_agent", safety_node)
workflow.add_node("coordinator", coordinator_node)
workflow.add_node("routing_agent", routing_node)
workflow.add_node("appointment_agent", appointment_node)
workflow.add_node("intake_agent", intake_node)
workflow.add_node("tools", ToolNode([
    book_appointment, 
    fetch_available_slots, 
    cancel_appointment, 
    reschedule_appointment, 
    list_patient_appointments,
    register_patient,
    classify_and_store_document,
    extract_document_metadata,
    update_patient_record,
    audit_required_forms
]))
workflow.add_node("document_agent", document_node)

workflow.set_entry_point("safety_agent")
workflow.add_edge("safety_agent", "coordinator")

# Add Conditional Edges from the Routing Agent
# FIXED: Added intake_agent to the routing map
workflow.add_conditional_edges(
    "coordinator",
    routing_node,
    {
        "appointment_agent": "appointment_agent",
        "intake_agent": "intake_agent",
        "document_agent": "document_agent",
        "safety_agent": "safety_agent",
        END: END
    }
)

def route_tool_return(state: dict):
    """Routes the graph back to the agent that called the tool."""
    current_task = state.get("current_task")
    
    if current_task == "intake_agent":
        return "intake_agent"
    elif current_task == "appointment_agent":
        return "appointment_agent"
    elif current_task == "document_agent":
        return "document_agent"
    
    # Fallback just in case
    return "appointment_agent"

# Define the Agent-Tool Loop
# tools_condition automatically checks if the LLM output contains 'tool_calls'. 
# If it does, it routes to "tools". If it doesn't, it routes to END.

# Add the Document Agent node (passing the bound llm or handling it inside the node)

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

# # Route from tools BACK to the correct agent
workflow.add_conditional_edges(
    "tools",
    route_tool_return
)

workflow.add_conditional_edges(
    "document_agent",
    tools_condition,
    {"tools": "tools", "__end__": END}
)

# FIXED: Deleted the two static add_edge("tools", ...) lines from here.

# Add a Memory Saver to the Graph
memory = MemorySaver()

# Compile the Graph
app_graph = workflow.compile(checkpointer=memory)

print(app_graph.get_graph(xray=True).draw_ascii())