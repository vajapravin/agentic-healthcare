import os

# Keep only the last 6 messages to prevent token explosion
MAX_HISTORY = 6

def load_prompt(filename: str) -> str:
    """
    Safely loads a system prompt from the prompts directory.
    This utility can be imported by any agent in the system.
    """
    # Navigate up from core/ to the backend root, then into prompts/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(current_dir, "..", "prompts", filename)
    
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"🚨 System prompt '{filename}' not found at {filepath}")

def trim_messages(state: dict):
    messages = state.get("messages", [])
    if len(messages) > MAX_HISTORY:
        # Keep system message if present, plus the most recent messages
        state["messages"] = messages[-MAX_HISTORY:]
    return state