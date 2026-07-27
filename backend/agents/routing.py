import re
import inspect
from core.llm import llm
from langgraph.graph import END
from core.db import SessionLocal
from core.models.department import Department
from core.utils import load_prompt  # Importing the shared utility
from langchain_core.prompts import ChatPromptTemplate

def routing_node(state: dict) -> dict:
    """
    Analyzes the message, queries departments, invokes the routing LLM,
    parses the destination, and routes directly using LangGraph Command.
    """
    messages = state.get("messages", [])
    lower_text = messages[-1].content.lower() if messages else ""

    # Attempt XML Tag Extraction
    match = re.search(r"<route>(.*?)</route>", lower_text)
    if match:
        extracted = match.group(1).strip()
        if extracted in ["appointment_agent", "intake_agent", "safety_agent", "document_agent"]:
            destination = extracted
    else:
        # Fallback keyword matching
        if "appointment" in lower_text:
            destination = "appointment_agent"
        elif "intake" in lower_text or "register" in lower_text or "patient" in lower_text:
            destination = "intake_agent"
        elif "document" in lower_text or "upload" in lower_text:
            destination = "document_agent"
        elif "emergency" in lower_text or "safety" in lower_text:
            destination = "safety_agent"
        else:
            destination = END
        
    print(f"--- ROUTING FINAL DECISION: '{destination}' ---")
    return destination
