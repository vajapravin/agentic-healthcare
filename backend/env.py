from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env.

LLM_MODEL_NAME=os.getenv("LLM_MODEL_NAME", None)
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", None)
DATABASE_URL=os.getenv("DATABASE_URL", None)

required_env_vars = [
    "LLM_MODEL_NAME",
    "OPENAI_API_KEY",
    "DATABASE_URL",
]

for var in required_env_vars:
    if not var:
        raise ValueError(f"🚨 Missing required environment variable: {var}")