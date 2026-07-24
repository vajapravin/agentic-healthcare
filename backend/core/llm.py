from langchain_openai import ChatOpenAI
from env import LLM_MODEL_NAME

llm = ChatOpenAI(
    model=LLM_MODEL_NAME,
    temperature=0,
    max_retries=5,          # Automatically retries on rate limits / server errors
    request_timeout=30
)