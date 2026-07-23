import re

def route_next_step(state: dict) -> str:
    """
    Parses the last message from the Coordinator.
    Attempts to find an XML tag, but falls back to keyword matching 
    if the LLM is being conversational.
    """
    messages = state.get("messages", [])
    if not messages:
        return "end"
    
    # Grab the text and convert to lowercase to avoid case-sensitivity bugs
    last_message = messages[-1].content.lower()
    
    # ATTEMPT 1: Strict XML Tag Extraction
    match = re.search(r"<route>(.*?)</route>", last_message)
    if match:
        destination = match.group(1).strip()
        if destination in ["appointment_agent", "intake_agent"]:
            return destination
            
    # ATTEMPT 2: Fallback Keyword Matching
    # If the LLM forgot the tag but mentioned the intent, route it anyway.
    if "intake_agent" in last_message or "register" in last_message or "intake" in last_message:
        return "intake_agent"
    
    if "appointment_agent" in last_message or "schedule" in last_message or "book" in last_message or "cancel" in last_message:
        return "appointment_agent"
        
    # If all else fails, end the graph
    return "end"