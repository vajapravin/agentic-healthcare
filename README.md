# Agentic Healthcare

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white) ![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white) ![LangGraph](https://img.shields.io/badge/LangGraph-333333?style=for-the-badge&logo=graphql&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white) ![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white) ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlite&logoColor=white) ![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</div>

A stateful, multi-agent backend architecture designed to autonomously handle healthcare administrative tasks, scheduling, and patient interactions. Built with Python, LangGraph, and FastAPI, this system utilizes a Supervisor/Specialist routing pattern to process natural language intents, execute Python tools, and perform CRUD operations against a live PostgreSQL database.

## 🏗 Architecture

The application uses a graph-based multi-agent architecture (via LangGraph) to ensure deterministic state management and reliable tool execution:

1. **State & Memory (`MemorySaver`)**: Intercepts incoming requests and retrieves conversational history based on a unique `thread_id`, enabling multi-turn, stateful interactions across isolated HTTP requests.
2. **Coordinator Agent (Supervisor)**: Acts as the entry point ("Front Desk"). It evaluates user intent, handles basic chit-chat, and routes complex requests using strict `<route>` XML tags.
3. **Routing Node**: A pure Python conditional edge that parses the supervisor's tags and directs the execution graph to the appropriate specialist agent.
4. **Appointment Agent (Specialist)**: Handles scheduling logistics. It features dynamic prompt injection (anchoring the LLM to real-world time) and uses LLM function-calling to execute deterministic database tools.

## ✨ Core Features

* **Intelligent Routing**: Avoids unnecessary LLM tool execution by terminating simple queries early and only invoking specialist nodes when domain-specific logic is required.
* **Autonomous Database Operations (CRUD)**:
  * `fetch_available_slots`: Queries live SQL data, handles Python/PostgreSQL timezone formatting, and resolves scheduling conflicts.
  * `book_appointment`: Inserts new records while validating foreign key constraints.
  * `cancel_appointment`: Safely verifies and deletes existing database records.
* **Temporal Awareness**: Injects system date and time into the context window, preventing common LLM hallucinations regarding relative terms like "tomorrow" or "next week."
* **Fully Containerized**: Backend runs entirely inside Docker, exposing a clean REST API via FastAPI and Uvicorn.

# Microsoft Presidio Integration for Local PII Redaction

This project integrates **Microsoft Presidio** to ensure robust, local data privacy and protection of Protected Health Information (PII) before any user input is processed by external LLM APIs.

## 🔒 How PII Redaction Works

1. **Interception at Entry:** Every incoming user message hits the local safety layer (`safety_agent`) before reaching the Coordinator or specialized agents.
2. **Local Analysis & Anonymization:** 
   * Presidio Analyzer scans the text locally (leveraging spaCy models) to identify sensitive entities such as `PERSON`, `PHONE_NUMBER`, and `EMAIL_ADDRESS`.
   * Presidio Anonymizer replaces the detected entities with standardized placeholder tokens (e.g., `<PERSON>`).
3. **External API Safety:** Only the fully scrubbed text is passed into external LLM context windows, preventing raw sensitive data from leaking to third-party providers.

---

## 🔑 Session-Based Token Mapping

To balance strict data privacy with functional backend persistence (such as writing patient names to Supabase), the system utilizes session-based token mapping:

* **State Tracking:** The safety node automatically populates and tracks a `pii_mapping` dictionary within the LangGraph thread state (e.g., mapping `{"<PERSON>": "John Smith"}`).
* **Secure Backend Unmasking:** When internal backend tools or trusted agent nodes (like the intake agent) need to commit data to the database, they resolve the placeholder token against the session state, ensuring real, unmasked data is safely stored locally without ever exposing it upstream to the LLM.

## 🚀 Getting Started

### Prerequisites
* Docker and Docker Compose installed.
* An active Supabase project with required tables (`patients`, `appointments`) configured.
* An OpenAI API key.

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/vajapravin/agentic-healthcare.git
   cd agentic-healthcare
   ```

2. **Configure Environment Variables:**
   Create a `.env` based on .env.example

3. **Build and Run with Docker Compose:**
   ```bash
   docker-compose up --build -d
   ```

4. **Verify the API:**
   Once running, the FastAPI backend will be available at `http://localhost:8000`. You can access the interactive Swagger documentation to test endpoints and chat threads at:
   ```text
   http://localhost:8000/docs