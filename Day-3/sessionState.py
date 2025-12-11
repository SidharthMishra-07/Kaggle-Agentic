import os
import asyncio
import json
import uuid
from dotenv import load_dotenv

from typing import Any, Dict

from google.adk.agents import Agent, LlmAgent
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.models.google_llm import Gemini
from google.adk.sessions import DatabaseSessionService
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools.tool_context import ToolContext
from google.genai import types

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

APP_NAME = "default"  # Application
USER_ID = "default"  # User
SESSION = "default"  # Session
MODEL_NAME = "gemini-2.5-flash-lite"

# Define helper functions
async def run_session(
    runner_instance: Runner,
    user_queries: list[str] | str = None,
    session_name: str = "default",
):
    print(f"\n ### Session: {session_name}")

    # Get app name from the Runner
    app_name = runner_instance.app_name

    # Attempt to create a new session or retrieve an existing one
    try:
        session = await session_service.create_session(
            app_name=app_name, user_id=USER_ID, session_id=session_name
        )
    except:
        session = await session_service.get_session(
            app_name=app_name, user_id=USER_ID, session_id=session_name
        )
    # Process queries if provided
    if user_queries:
        # Convert single query to list for uniform processing
        if type(user_queries) == str:
            user_queries = [user_queries]

        # Process each query in the list sequentially
        for query in user_queries:
            print(f"\nUser > {query}")

            # Convert the query string to the ADK Content format
            query = types.Content(role="user", parts=[types.Part(text=query)])

            # Stream the agent's response asynchronously
            async for event in runner_instance.run_async(
                user_id=USER_ID, session_id=session.id, new_message=query
            ):
                # Check if the event contains valid content
                if event.content and event.content.parts:
                    # Filter out empty or "None" responses before printing
                    if (
                        event.content.parts[0].text != "None"
                        and event.content.parts[0].text
                    ):
                        print(f"{MODEL_NAME} > ", event.content.parts[0].text)
    else:
        print("No queries!")


retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

USER_NAME_SCOPE_LEVELS = ("temp", "user", "app")

APP_NAME = "default"
USER_ID = "default"
MODEL_NAME = "gemini-2.5-flash-lite"


def save_info(tool_context: ToolContext, user_name: str, country: str) -> Dict[str, Any]:
    """ 
        Tool to save and store username and country in session state

        Args:
            user_name (str): The name of the user
            country (str): The country of the user

        Returns:
            Dict[str, Any]: The updated session state
    """

    tool_context.state["user: name"] = user_name
    tool_context.state["user: country"] = country

    return {"status": "success"}

def retrieve_user_info(tool_context: ToolContext) -> Dict[str, Any]:
    """ 
        Tool to retrieve and return username and country from session state

        Args:
            tool_context (ToolContext): The tool context

        Returns:
            Dict[str, Any]: The session state
    """
    user_name = tool_context.state.get("user: name", "username not found")
    country = tool_context.state.get("user: country", "country not found")

    return {"status":"success", "user_name": user_name, "country": country}

root_agent = LlmAgent(
    name="text_chat_bot",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    description = "A text chatbot",
    instruction = "Your task to answer the user's queries and store the user's name and country in session state when provided using the tool 'save_info' and retrieve the user's name and country from session state when provided using the tool 'retrieve_user_info'.",
    tools = [save_info, retrieve_user_info]
)

session_service = InMemorySessionService()

runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

async def main():
    await run_session(
        runner,
        ["Hi there, how are you doing today? What is my name?",  # Agent shouldn't know the name yet
        "My name is Sid. I'm from India.",  # Provide name - agent should save it
        "What is my name? Which country am I from?",  # Agent should recall from session state
        ],
        # [
        #     "Hi there, how are you doing today? What is my name?"
        # ],
    "sessionState-session-01",
    )

    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id="sessionState-session-01",
    )
    print(f"\nSession State: {session.state}")

if __name__ == "__main__":
    asyncio.run(main())
