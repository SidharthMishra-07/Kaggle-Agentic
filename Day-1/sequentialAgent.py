#Blog Post Creation with Sequential Agents

from json import tool
import os
import asyncio
import wikipedia
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

@FunctionTool
def search_wikipedia(query: str) -> str:
    """Search Wikipedia and return a summary for the given query.""" #Docstring
    try:
        summary = wikipedia.summary(query, sentences=3)
        return summary
    except Exception as e:
        return f"Error fetching Wikipedia data: {e}"

print("✅ Wikipedia tool created.")

#Define sub-agent

# Outline Agent: Creates the initial blog post outline.
outline_agent = Agent(
    name="OutlineAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""Create a blog outline for the given topic with:
    1. A catchy headline
    2. An introduction hook
    3. 3-5 main sections with 2-3 bullet points for each
    4. A concluding thought""",
    output_key="blog_outline",  # The result of this agent will be stored in the session state with this key.
)

print("✅ outline_agent created.")

# Writer Agent: Writes the full blog post based on the outline from the previous agent.
writer_agent = Agent(
    name="WriterAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""Follwing this outline strictly {blog_outline}
    Write a brief, 200 to 300-word blog post with an engaging and informative tone using the search wikipedia tool""",
    tools=[search_wikipedia],
    output_key= "blog_draft"
)
print("✅ writer_agent created.")


# Editor Agent: Edits and polishes the draft from the writer agent.
editor_agent = Agent(
    name="EditorAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    # This agent receives the `{blog_draft}` from the writer agent's output.
    instruction="""Edit this draft: {blog_draft}
    Your task is to polish the text by fixing any grammatical errors, improving the flow and sentence structure, and enhancing overall clarity.""",
    output_key="final_blog"
)
print("✅ editor_agent created.")

root_agent = SequentialAgent(
    name= "BlogPipeline",
    sub_agents=[outline_agent, writer_agent, editor_agent]
)
print("✅ Sequential Agent created.")


runner = InMemoryRunner(agent=root_agent)

async def main():
    response = await runner.run_debug(
    "Write a blog on Amdocs"
    )

asyncio.run(main())