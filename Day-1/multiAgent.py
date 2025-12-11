import os
import asyncio
from dotenv import load_dotenv

from google.adk.agents import Agent, SequentialAgent, ParallelAgent, LoopAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool, FunctionTool, google_search
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

#Define sub-agent

research_agent = Agent(
    name = "Researcher",
    model = Gemini(
        model="gemini-2.5-flash-lite",
        retry_options= retry_config
    ),
    instruction= """You are a specialized research agent. Your only job is to use the
    google_search tool to find 2-3 pieces of relevant information on the given topic and present the findings""",
    tools=[google_search],
    output_key="research_findings" # The result of this agent will be stored in the session state with this key.
)
print("✅ research_agent created.")


summariser_agent = Agent(
    name = "SummariserAgent",
    model = Gemini(
        model = "gemini-2.5-flash-lite",
        retry_options= retry_config
    ),
    instruction="""You are tasked with reading the following reserach result : {research_findings} 
    Create a consise summmary as a bulleted list with 3-5 key points""",
    output_key="final_summary" 
)

print("✅ summarizer_agent created.")

root_agent = Agent(
    name = "Coordinator",
    model = Gemini(
        model = "gemini-2.5-flash-lite",
        retry_options= retry_config
    ),
    instruction="""You are the research Coordinator. Your goal is to answer the user's query by orchestrarting a workflow.
    1. First you MUST call the 'Reasearcher' tool to find relevant information on the topic provided by the user.
    2. Next, after receiving hte research findings, you MUSt call the 'SummariserAgent' to create a summary for the research findings
    3. Finally present the final summary as your response as the final output to the user. """,
    tools = [AgentTool(research_agent), AgentTool(summariser_agent)],
)

print("✅ root_agent created.")

runner  = InMemoryRunner(agent=root_agent)

async def main():
    response = await runner.run_debug(
        "Explain policies of Amdocs"
    )

# Run the async function
asyncio.run(main())