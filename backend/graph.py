from langgraph.graph import StateGraph, END
from state import AgentState

# 1. Define Node Functions (The logic for each step)
def router_node(state: AgentState):
    """Analyzes the request and decides the next step."""
    # For now, we just pass a simple message back to prove it works
    print(f"Router received: {state['messages'][-1].content}")
    
    return {
        "messages": [{"role": "assistant", "content": "I am the router. I hear you!"}],
        "current_task": "triage",
        "task_status": "in_progress"
    }

# 2. Initialize the Graph using your AgentState
workflow = StateGraph(AgentState)

# 3. Add Nodes to the Graph
# (Name of the node, Function to execute)
workflow.add_node("router", router_node)

# 4. Define the Edges (The flow of the graph)
workflow.set_entry_point("router")
workflow.add_edge("router", END) # The graph stops after the router for now

# 5. Compile the Graph
# This turns the definition into an executable application
app_graph = workflow.compile()