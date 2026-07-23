from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from langchain_core.messages import HumanMessage

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def safety_node(state: dict):
    messages = state.get("messages", [])
    if not messages:
        return {"messages": messages}
    
    last_message = messages[-1]
    
    # Grab existing mapping or initialize a new one for this thread
    pii_mapping = state.get("pii_mapping", {})
    
    if hasattr(last_message, 'content') and last_message.type == "human":
        original_text = last_message.content
        
        # Analyze for PII
        results = analyzer.analyze(
            text=original_text, 
            entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS"], 
            language='en'
        )
        
        # Anonymize text
        anonymized_result = anonymizer.anonymize(
            text=original_text, 
            analyzer_results=results
        )
        
        scrubbed_text = anonymized_result.text
        
        # Map any newly generated placeholder back to the original text snippet
        # Presidio generates items like <PERSON>. Let's track them.
        for item in anonymized_result.items:
            entity_type = item.entity_type
            # Extract the substring from the original text that matched
            start = item.start
            end = item.end
            original_value = original_text[start:end]
            
            # Create the standard placeholder token Presidio uses
            placeholder = f"<{entity_type}>"
            pii_mapping[placeholder] = original_value
            
        messages[-1] = HumanMessage(content=scrubbed_text)
        
    return {
        "messages": messages,
        "current_task": "safety_agent",
        "pii_mapping": pii_mapping
    }