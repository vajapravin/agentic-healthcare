import os
from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage

from core.utils import load_prompt  # Importing the shared utility
from env import LLM_MODEL_NAME  # Importing the validated variable

# 1. Define the Strict Output Schema using Pydantic
class CoordinatorOutput(BaseModel):
    message_to_user: str = Field(
        description="The conversational response or clarifying question to show the user."
    )
    next_node: Literal[
        "appointment_agent", 
        "document_agent", 
        "routing_agent", 
        "followup_agent", 
        "safety_agent", 
        "end"
    ] = Field(
        description="The precise name of the next agent to route to. Choose 'end' if the workflow is complete or waiting for user input."
    )

# 2. Initialize the LLM
# We use temperature=0 because the Coordinator needs to make strict, deterministic 
# routing decisions, not creative guesses.
# (Ensure OPENAI_API_KEY is loaded in your .env file)
llm = ChatOpenAI(model=LLM_MODEL_NAME, temperature=0)
structured_llm = llm.with_structured_output(CoordinatorOutput)

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

    output: CoordinatorOutput = structured_llm.invoke(invocation_messages)

    # 4. Invoke the LLM
    ai_response = AIMessage(content=output.message_to_user)

    print(f" -> Routing Decision: {output.next_node}")
    
    # 5. Return the state update
    # Because of our reducer in state.py (Annotated[list, add_messages]),
    # returning a dict with "messages" will append this new response to the history.
    return {
        "messages": [ai_response],
        "current_task": output.next_node  # Update the current task for routing
    }