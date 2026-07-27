import inspect
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from langchain_core.messages import HumanMessage, AIMessage

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

EMERGENCY_KEYWORDS = ["chest pain", "suicide", "bleed", "emergency", "unconscious", "severe allergic reaction"]

def safety_node(state: dict):
    print(f"{'#'*50}{__file__}#safety_node:{inspect.currentframe().f_lineno}: {locals()}")

    messages = state.get("messages", [])
    if not messages:
        return {"messages": messages}
    
    last_message = messages[-1]
    pii_mapping = state.get("pii_mapping", {})
    
    # Only scan human messages for PII and emergencies
    if hasattr(last_message, 'content') and last_message.type == "human":
        original_text = last_message.content
        lower_text = original_text.lower()
        
        # 1. Check for emergency keywords
        is_emergency = any(keyword in lower_text for keyword in EMERGENCY_KEYWORDS)
        if is_emergency:
            emergency_response = AIMessage(
                content="EMERGENCY NOTICE: It sounds like you are experiencing a medical emergency. Please call emergency services (911 or local emergency number) immediately or go to the nearest hospital."
            )
            return {
                "messages": [emergency_response],
                "current_task": "safety_agent",
                "pii_mapping": pii_mapping
            }

        # 2. Analyze PII using Presidio
        analysis_results = analyzer.analyze(
            text=original_text, 
            entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS"], 
            language='en'
        )
        
        # 3. Anonymize/Mask text if PII is found
        if analysis_results:
            anonymized_result = anonymizer.anonymize(
                text=original_text,
                analyzer_results=analysis_results
            )
            masked_text = anonymized_result.text
            
            # Create a new HumanMessage with the scrubbed text to pass down the graph
            scrubbed_message = HumanMessage(content=masked_text, id=last_message.id)
            
            # Optionally update state messages list replacing or appending
            return {
                "messages": [scrubbed_message],
                "current_task": "routing", # or keep normal flow
                "pii_mapping": pii_mapping
            }

    # Default passthrough if no changes needed
    return {
        "messages": [],
        "current_task": "routing",
        "pii_mapping": pii_mapping
    }