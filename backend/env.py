from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env.

LLM_MODEL_NAME=os.getenv("LLM_MODEL_NAME", None)

required_env_vars = [
    "LLM_MODEL_NAME",
]

for var in required_env_vars:
    if not var:
        raise ValueError(f"🚨 Missing required environment variable: {var}")