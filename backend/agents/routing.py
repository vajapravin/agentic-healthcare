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

    print(f"--- route_next_step::LAST MESSAGE: {last_message} ---")
    
    # ATTEMPT 1: Strict XML Tag Extraction
    match = re.search(r"<route>(.*?)</route>", last_message)
    if match:
        destination = match.group(1).strip()
        print(f"--- ROUTING: Extracted route -> {destination} ---")
        if destination in ["appointment_agent", "intake_agent", "safety_agent"]:
            return destination
            
    # ATTEMPT 2: Fallback Keyword Matching on the string (using last_message)
    if "appointment" in last_message:
        destination = "appointment_agent"
    elif "intake" in last_message or "register" in last_message or "patient" in last_message:
        destination = "intake_agent"
    elif "emergency" in last_message or "safety" in last_message:
        destination = "safety_agent"
    else:
        destination = "end"
        
    print(f"--- ROUTING FINAL DECISION: '{destination}' ---")
    return destination