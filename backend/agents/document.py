from langchain_core.messages import SystemMessage
from core.utils import load_prompt
from core.llm import llm
from tools.documents import classify_and_store_document, extract_document_metadata, update_patient_record, audit_required_forms

document_tools = [classify_and_store_document, extract_document_metadata, update_patient_record, audit_required_forms]  # List of document-related tools
document_llm = llm.bind_tools(document_tools)  # Bind the tools to the LLM

def document_node(state: dict) -> dict:
    print("--- EXEC: Document Agent ---")
    
    # Load prompt directly using your project's helper
    system_prompt_text = load_prompt("document.md")
    messages = state.get("messages", [])
    
    invocation_messages = [SystemMessage(content=system_prompt_text)] + messages
    
    # Invoke the LLM (using your llm bound with tools)
    response = document_llm.invoke(invocation_messages)
    
    return {
        "messages": [response],
        "current_task": "document_coordination_handled"
    }