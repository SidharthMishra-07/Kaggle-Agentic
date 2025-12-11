import os
import asyncio
from typing import List, Union, Any

from dotenv import load_dotenv
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.tools import preload_memory

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("🔑 GOOGLE_API_KEY not found in .env file")

# Configuration
APP_NAME = "MemoryDemoApp"
USER_ID = "default"
MODEL_NAME = "gemini-2.5-flash-lite"


async def run_session(
    runner_instance: Runner, user_queries: Union[List[str], str], session_id: str = "default"
) -> None:
    """Helper function to run queries in a session and display responses."""
    print(f"\n### Session: {session_id}")

    # Create or retrieve session
    try:
        session = await session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
    except Exception:
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )

    # Convert single query to list
    if isinstance(user_queries, str):
        user_queries = [user_queries]

    # Process each query
    for query in user_queries:
        print(f"\nUser > {query}")
        query_content = types.Content(role="user", parts=[types.Part(text=query)])

        # Stream agent response
        async for event in runner_instance.run_async(
            user_id=USER_ID, session_id=session.id, new_message=query_content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                text = event.content.parts[0].text
                if text and text != "None":
                    print(f"Model: > {text}")

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# Initialize Services
memory_service = InMemoryMemoryService()
session_service = InMemorySessionService()

async def auto_save_to_memory(callback_context):
    """Automatically save session to memory after each agent turn."""
    await callback_context._invocation_context.memory_service.add_session_to_memory(
        callback_context._invocation_context.session
    )

auto_user_agent = LlmAgent(
    name="MemoryDemoAgent",
    model=Gemini(
        model=MODEL_NAME,
        retry_options=retry_config
    ),
    instruction="Answer user questions in simple words.",
    tools=[preload_memory],
    after_agent_callback=auto_save_to_memory
)

runner = Runner(
    agent=auto_user_agent,
    app_name=APP_NAME,
    session_service=session_service,
    memory_service=memory_service
)

async def main():
    await run_session(
        runner,
        "I gifted a new Hotwheels car to my nephew on his 1st birthday!",
        "autosave-test-01",
    )

    await run_session(
        runner,
        "What did I gift to my nephew on his 1st birthday?",
        "autosave-test-02",
    )

if __name__ == "__main__":
    asyncio.run(main())
