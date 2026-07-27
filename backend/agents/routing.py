import re
import inspect
from rich import inspect
from core.llm import llm
from core.db import SessionLocal
from core.models.department import Department
from core.utils import load_prompt  # Importing the shared utility
from langchain_core.prompts import ChatPromptTemplate

def routing_node(state: dict) -> dict:
    """
    Analyzes the message, queries departments, invokes the routing LLM,
    parses the destination, and routes directly using LangGraph Command.
    """
    # db = SessionLocal()
    # departments = db.query(Department).filter(Department.active == True).all()
    # db.close()
    
    # dept_str = "\n".join([f"- ID: {d.id} | Name: {d.name} | Description: {d.description}" for d in departments])

    # # 1. Load instructions from routing.md
    # system_prompt_text = load_prompt("routing.md")

    # template = ChatPromptTemplate.from_messages([
    #     ("system", system_prompt_text),
    #     ("placeholder", "{messages}")
    # ])
    
    messages = state.get("messages", [])
    lower_text = messages[-1].content.lower() if messages else ""

    # formatted_prompt = template.invoke({
    #     "departments_list": dept_str,
    #     "input": latest_input
    # })

    # # 2. Invoke LLM
    # response = llm.invoke(formatted_prompt)
    # response_text = response.content
    # lower_text = response_text.lower()

    # print(f"--- LLM Response: {response_text} ---")

    # 3. Parse destination inline (similar to your route_next_step logic)
    destination = state["current_task"]  # default fallback
    
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
        
    print(f"--- ROUTING FINAL DECISION: '{destination}' ---")
    return destination
