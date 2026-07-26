from langchain_core.messages import SystemMessage
from core.utils import load_prompt
from core.llm import llm
from tools.appointments import book_appointment, fetch_available_slots

# 1. Bind tools relevant for scheduling follow-up visits
followup_tools = [book_appointment, fetch_available_slots]
followup_llm = llm.bind_tools(followup_tools)

# 2. Define the graph node function expected by graph.py
def followup_node(state: dict) -> dict:
    print("--- EXEC: Follow-up Agent ---")
    
    # Load prompt from prompts/followup.md
    system_prompt_text = load_prompt("followup.md")
    messages = state.get("messages", [])

    invocation_messages = [SystemMessage(content=system_prompt_text)] + messages
    
    # Invoke the LLM with bound follow-up tools
    response = followup_llm.invoke(invocation_messages)
    
    return {
        "messages": [response],
        "current_task": "followup_scheduled"
    }