import os
import asyncio
import json
import uuid
from dotenv import load_dotenv

from typing import Any, Dict

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.tools import load_memory, preload_memory
from google.genai import types

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("🔑 GOOGLE_API_KEY not found in .env file")

APP_NAME = "MemoryDemoApp" 
USER_ID = "default"  
SESSION = "default"  
MODEL_NAME = "gemini-2.5-flash-lite"

# Define helper functions
async def run_session(
    runner_instance: Runner, user_queries: list[str] | str, session_id: str = "default"
):
    """Helper function to run queries in a session and display responses."""
    print(f"\n### Session: {session_id}")

    # Create or retrieve session
    try:
        session = await session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
    except:
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
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

user_agent = LlmAgent(
    name="MemoryDemoAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite", 
        retry_options=retry_config
        ),
    instruction="Answer user questions in simple words. Use load_memory tool if you need to recall past conversations.",
    tools=[preload_memory]
)

memory_service = InMemoryMemoryService()
session_service = InMemorySessionService()

runner = Runner(agent=user_agent, app_name=APP_NAME, session_service=session_service, memory_service=memory_service)

# Configuration vs Usage: Adding memory_service to the Runner makes memory available to your agent, but doesn't automatically use it. You must explicitly:
    # Ingest data using add_session_to_memory()
    # Enable retrieval by giving your agent memory tools (load_memory or preload_memory)

async def main():
    # await run_session(
    #     runner,
    #     ["My favorite color is blue-green. Can you write a Haiku about it?"],
    # "agentMemory-01",
    # )

    await run_session(
        runner,
        ["My Birthday is on 16th April. Can you remind me?"],
    "birthday-test",
    )

    session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id="birthday-test")
    # print("\nSession contains:")
    # for event in session.events:
    #     text = (
    #         event.content.parts[0].text[:60]
    #         if event.content and event.content.parts
    #         else "(empty)"
    #     )
    #     print(f"{event.content.role}: {text}...")

    await memory_service.add_session_to_memory(session)
    print("Session added to memory!")

    search_response = await memory_service.search_memory(
    app_name=APP_NAME, user_id=USER_ID, query="What is the user's birthday?"
    )

    print("Search Results:")
    print(f"Found {len(search_response.memories)} relevant memories")
    print()

    for memory in search_response.memories:
        if memory.content and memory.content.parts:
            text = memory.content.parts[0].text[:80]
            print(f"[{memory.author}]: {text}...")


if __name__ == "__main__":
    asyncio.run(main())

