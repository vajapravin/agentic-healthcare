from fastapi import FastAPI
from pydantic import BaseModel
from graph import app_graph
from langchain_core.messages import HumanMessage

# Import the compiled graph we built in the previous steps
# Adjust the import path if your workflow.py is located elsewhere
app = FastAPI(title="Agentic Healthcare API")

# Define the expected input from the frontend
class ChatRequest(BaseModel):
    message: str

@app.get("/")
def health_check():
    return {"status": "Backend is running flawlessly!"}


@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    """
    Takes the user's message, passes it to the LangGraph state machine, 
    and returns the final response and routing decision.
    """

    # 1. Package the user's input into the exact format AgentState expects
    initial_state = {
        "messages": [HumanMessage(content=request.message)]
    }

    # 2. Run the LangGraph state machine
    # This will trigger the Coordinator, which will then trigger the routing
    result = app_graph.invoke(initial_state)
    
    # 3. Extract the latest AI message from the state
    # result["messages"] is a list of the whole conversation, so we grab the last item [-1]
    final_ai_message = result["messages"][-1].content
    
    # 4. Extract the routing decision
    current_task = result.get("current_task", "end")
    
    return {
        "response": final_ai_message,
        "current_task": current_task
    }