from fastapi import FastAPI, Request
from core.logger import setup_logger
import traceback
from pydantic import BaseModel
from graph import app_graph
from langchain_core.messages import HumanMessage
from routers.documents import router as document_router
from contextlib import asynccontextmanager
# Import engine and the models package
from core.db import engine
from core import models
from core.utils import print_startup_banner

@asynccontextmanager
async def lifespan(app: FastAPI):
    print_startup_banner()
    logger.info("AgentCare Backend initialized and ready for requests.")
    yield
    logger.info("AgentCare Backend is shutting down.")

# Create tables if they don't exist
models.Base.metadata.create_all(bind=engine)

# Import the compiled graph we built in the previous steps
# Adjust the import path if your workflow.py is located elsewhere
app = FastAPI(title="Agentic Healthcare API", version="1.0.0", lifespan=lifespan)
app.include_router(document_router)

logger = setup_logger("agentic_healthcare_api")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code} for {request.method} {request.url}")
        return response
    except Exception as e:
        logger.error(f"Unhandled exception on {request.method} {request.url}: {str(e)}")
        logger.error(traceback.format_exc())
        raise e

# Define the expected input from the frontend
class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default_thread_1" # Optional: default thread ID if not provided

@app.get("/")
def health_check():
    return {"status": "Backend is running flawlessly!"}

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    """
    Takes the user's message, passes it to the LangGraph state machine, 
    and returns the final response and routing decision.
    """

    logger.debug(f"Chat payload received: {request}")

    # 1. Package the user's input into the exact format AgentState expects
    initial_state = {
        "messages": [HumanMessage(content=request.message)]
    }

    # 2. Run the LangGraph state machine
    # This will trigger the Coordinator, which will then trigger the routing
    config = {"configurable": {"thread_id": request.thread_id}}
    result = app_graph.invoke(initial_state, config=config)
    
    # 3. Extract the latest AI message from the state
    # result["messages"] is a list of the whole conversation, so we grab the last item [-1]
    final_ai_message = result["messages"][-1].content
    
    # 4. Extract the routing decision
    current_task = result.get("current_task", "unknown")
    
    return {
        "response": final_ai_message,
        "current_task": current_task,
        "thread_id": request.thread_id
    }