import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search
from google.genai import types

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("🔑 GOOGLE_API_KEY not found in .env file")

# Retry configuration
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504]
)

# Define the agent
root_agent = Agent(
    name="Searcher",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    description="A simple agent to answer GK questions",
    instruction="You are a helpful assistant. Use Google Search for current info or if unsure.",
    tools=[google_search]
)
print("✅ Root Agent defined.")

# Create runner
runner = InMemoryRunner(agent=root_agent)
print("✅ Runner created.")

# Async execution
async def main():
    response = await runner.run_debug(
        "Who is the CEO of AMDOCS?"
    )

# Run the async function
asyncio.run(main())