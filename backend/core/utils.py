import os
import pyfiglet

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

def print_startup_banner():
    # Generate large ASCII text using standard slant font
    ascii_art = pyfiglet.figlet_format("Agentic HealthCare", font="slant")
    
    # ANSI Color Code: Bright Cyan / Blue
    cyan_color = "\033[96m"
    bold = "\033[1m"
    reset = "\033[0m"
    
    border = "=" * 60
    print(f"\n{cyan_color}{bold}{border}")
    print(ascii_art)
    print(f"Server is up and running successfully!")
    print(f"{border}{reset}\n")