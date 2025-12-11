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

tech_researcher = Agent(
    name = "Tech",
    model=Gemini(
        model = "gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""Research the latest AI/ML trends. Include 3 key developments,
    the main companies involved, and the potential impact. Keep the report very concise (100 words).""",
    tools=[google_search],
    output_key = "tech_research"
)

health_researcher = Agent(
    name = "Tech",
    model=Gemini(
        model = "gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""Research the latest medical trends. Include 3 key developments,
    the main companies involved, and the potential impact. Keep the report very concise (100 words).""",
    tools=[google_search],
    output_key = "health_research"
)

fin_researcher = Agent(
    name = "Tech",
    model=Gemini(
        model = "gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""Research the latest Finance trends. Include 3 key developments,
    the main companies involved, and the potential impact. Keep the report very concise (100 words).""",
    tools=[google_search],
    output_key = "fin_research"
)

aggregator_agent = Agent(
    name = 'Aggregator',
    model = Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""Combine these three research findings into a single executive summary
    {tech_research}, {health_research}, {fin_research}
    Your summary should highlight common themes, surprising connections, and the most important key takeaways from all three reports. The final summary should be around 200 words.""",
    output_key="final_summary"
)
print("✅ aggregator_agent created.")

# The ParallelAgent runs all its sub-agents simultaneously.
parallel_research = ParallelAgent(
    name = 'parallelResearch',
    sub_agents=[tech_researcher, health_researcher, fin_researcher]
)

# This SequentialAgent defines the high-level workflow: run the parallel team first, then run the aggregator.
root_agent = SequentialAgent(
    name = "ResearchSystem",
    sub_agents=[parallel_research, aggregator_agent]
)

runner = InMemoryRunner(agent=root_agent)

async def main():
    response = await runner.run_debug(
        "Run the daily executive briefing on Tech, Health, and Finance"
    )

asyncio.run(main())
