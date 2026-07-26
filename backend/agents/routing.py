import re
from langchain_core.prompts import ChatPromptTemplate
from core.llm import llm
from core.db import SessionLocal
from core.models.department import Department

def get_routing_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", """You are the Routing Agent for the AgentCare platform. 
Your task is to analyze the user's input, detect their administrative or clinical intent, and map them to the correct workflow destination.

Available Departments in System:
{departments_list}

Rules:
1. Identify if the user needs an appointment, patient intake/registration, document coordination, or safety review.
2. You MUST wrap your final routing decision inside exact XML tags, for example: <route>appointment_agent</route>, <route>intake_agent</route>, or <route>safety_agent</route>.
"""),
        ("human", "{input}")
    ])

def routing_node(state: dict) -> dict:
    """
    Analyzes the message and state to route the user to the correct workflow path.
    """
    db = SessionLocal()
    departments = db.query(Department).filter(Department.active == True).all()
    db.close()
    
    dept_str = "\n".join([f"- ID: {d.id} | Name: {d.name} | Description: {d.description}" for d in departments])
    
    prompt = get_routing_prompt().partial(departments_list=dept_str)
    
    messages = state.get("messages", [])
    latest_input = messages[-1].content if messages else ""
    
    chain = prompt | llm
    response = chain.invoke({"input": latest_input})
    
    # Append or track routing output in state while preserving chat flow
    return {
        "current_task": "routing_complete",
        "last_routing_decision": response.content
    }

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