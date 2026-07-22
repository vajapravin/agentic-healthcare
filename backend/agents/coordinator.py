import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from core.utils import load_prompt  # Importing the shared utility

# 1. Initialize the LLM
# We use temperature=0 because the Coordinator needs to make strict, deterministic 
# routing decisions, not creative guesses.
# (Ensure OPENAI_API_KEY is loaded in your .env file)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

def coordinator_node(state: dict) -> dict:
    """
    The main orchestrator node. 
    It reads the state, consults the system prompt, and generates a response.
    """
    print("--- EXEC: Coordinator Node ---")
    
    # 1. Load the explicit instructions for this agent
    system_prompt_text = load_prompt("coordinator.md")
    
    # 2. Retrieve the existing conversation from the state
    messages = state.get("messages", [])
    
    # 3. Construct the exact prompt for the LLM
    # We place the SystemMessage at the very top of the context window, 
    # followed by the entire user/assistant chat history.
    invocation_messages = [SystemMessage(content=system_prompt_text)] + messages
    
    # 4. Invoke the LLM
    response = llm.invoke(invocation_messages)
    
    # 5. Return the state update
    # Because of our reducer in state.py (Annotated[list, add_messages]),
    # returning a dict with "messages" will append this new response to the history.
    return {"messages": [response]}