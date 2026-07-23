def route_next_step(state: dict) -> str:
    """
    Reads the current_task from the state and routes the graph to the corresponding agent.
    If no task is set, it defaults to routing to the end.
    """
    current_task = state.get("current_task", "end")
    return current_task