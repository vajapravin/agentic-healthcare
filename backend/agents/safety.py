from presidio_analyzer import AnalyzerEngine
from langchain_core.messages import HumanMessage

analyzer = AnalyzerEngine()

EMERGENCY_KEYWORDS = ["chest pain", "suicide", "bleed", "emergency", "unconscious", "severe allergic reaction"]

def safety_node(state: dict):
    messages = state.get("messages", [])
    if not messages:
        return {"messages": messages}
    
    last_message = messages[-1]
    pii_mapping = state.get("pii_mapping", {})
    
    if hasattr(last_message, 'content') and last_message.type == "human":
        original_text = last_message.content
        
        # 1. Analyze for PII
        results = analyzer.analyze(
            text=original_text, 
            entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS"], 
            language='en'
        )
        
        # 2. Sort results by start index
        sorted_results = sorted(results, key=lambda x: x.start)
        merged_results = []
        
        # 3. Merge adjacent split name spans (e.g., merging "Rakesh" and "Bahl")
        for current in sorted_results:
            if merged_results and merged_results[-1].entity_type == "PERSON" and current.entity_type == "PERSON":
                prev = merged_results[-1]
                # If they are separated by just a space or punctuation, merge them
                if original_text[prev.end:current.start].strip() == "":
                    prev.end = current.end
                    prev.score = max(prev.score, current.score)
                    continue
            merged_results.append(current)

        # 4. Perform direct replacement in reverse order (highest index first) to prevent index shifting
        scrubbed_text = original_text
        sorted_items = sorted(merged_results, key=lambda x: x.start, reverse=True)
        
        entity_counters = {}
        for item in sorted_items:
            entity_type = item.entity_type
            start = item.start
            end = item.end
            original_value = original_text[start:end]
            
            # Skip empty spans just in case
            if start == end:
                continue
            
            count = entity_counters.get(entity_type, 0) + 1
            entity_counters[entity_type] = count
            
            placeholder = f"<{entity_type}_{count}>"
            pii_mapping[placeholder] = original_value
            
            # Directly replace the exact character span
            scrubbed_text = scrubbed_text[:start] + placeholder + scrubbed_text[end:]
            
        messages[-1] = HumanMessage(content=scrubbed_text)
        
    return {
        "messages": messages,
        "current_task": "safety_agent",
        "pii_mapping": pii_mapping
    }


def check_for_escalation(text: str) -> bool:
    lower_text = text.lower()
    return any(keyword in lower_text for keyword in EMERGENCY_KEYWORDS)


def create_follow_up_task(patient_id: int, task_description: str) -> str:
    return f"Follow-up task created for Patient ID {patient_id}: '{task_description}'."