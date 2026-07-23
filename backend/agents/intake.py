from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from env import LLM_MODEL_NAME
from core.utils import load_prompt
from tools.patients import register_patient

# 1. Initialize the LLM
llm = ChatOpenAI(model=LLM_MODEL_NAME, temperature=0)

# Define the tools for this specific agent
intake_tools = [register_patient]
intake_llm = llm.bind_tools(intake_tools)

def intake_node(state: dict):
    messages = state.get("messages", [])
    
    # Load the base prompt
    system_prompt_text = load_prompt("intake.md")
    
    # Bind the tools and invoke
    system_message = SystemMessage(content=system_prompt_text)
    response = intake_llm.invoke([system_message] + messages)
    
    return {
        "messages": [response],
        "current_task": "intake_agent"
    }