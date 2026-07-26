from langchain_core.messages import SystemMessage
from core.utils import load_prompt
from core.llm import llm
from tools.appointments import (
    book_appointment,
    fetch_available_slots,
    cancel_appointment,
    reschedule_appointment,
    list_patient_appointments
)

# 1. Bind tools to the LLM
appointment_tools = [
    book_appointment,
    fetch_available_slots,
    cancel_appointment,
    reschedule_appointment,
    list_patient_appointments
]
appointment_llm = llm.bind_tools(appointment_tools)

# 2. Define the exact function name expected by graph.py
def appointment_node(state: dict) -> dict:
    print("--- EXEC: Appointment Agent ---")
    
    system_prompt_text = load_prompt("appointment.md")
    messages = state.get("messages", [])

    invocation_messages = [SystemMessage(content=system_prompt_text)] + messages
    
    # Invoke the LLM
    response = appointment_llm.invoke(invocation_messages)
    
    return {
        "messages": [response],
        "current_task": "appointment_handled"
    }