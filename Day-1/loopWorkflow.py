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
API_Key = os.getenv("GOOGLE_API_KEY")
if not API_Key:
    raise ValueError("API Key not found")

# Retry configuration
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504]
)

def exit_loop():
    """ Call this agent ONLY when the critique is 'APPROVED', indicating the story is finished and no more changes are needed."""
    return {"status": "approved", "message" : "Story approved. Exiting refinement loop."}

exit_loop_tool = FunctionTool(exit_loop)

initial_writer_agent = Agent(
    name="InitialWriterAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""Based on the user's prompt, write the first draft of a short story (around 100-150 words).
    Output only the story text, with no introduction or explanation.""",
    output_key="current_story",  # Stores the first draft in the state.
)

print("✅ initial_writer_agent created.")


critic_agent = Agent(
    name="CriticAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""You are a constructive story critic. Review the story provided below.
    Story: {current_story}
    
    Evaluate the story's plot, characters, and pacing.
    - If the story is well-written and complete, you MUST respond with the exact phrase: "APPROVED"
    - Otherwise, provide 2-3 specific, actionable suggestions for improvement.""",
    output_key="critique",  # Stores the feedback in the state.
)

print("✅ critic_agent created.")

refiner_agent = Agent(
    name = "RefinerAgent",
    model = Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""You are a story refiner. You have a story draft and critique.
    Story Draft: {current_story}
    critique: {critique}

    Your task is to analyze the critique.
    - IF the critique is EXACTLY 'APPROVED', you must call the 'exit_loop' function tool and nothing else.
    - OTHERWISE, rewrite the story draft to fully incorporate the feedback from the critique.
    """,
    output_key="current_story",
    tools=[exit_loop_tool]
)


# Loop agent with exit condition
story_refinement_loop = LoopAgent(
    name="StoryRefiner",
    sub_agents=[critic_agent, refiner_agent],
    max_iterations=3
)


root_agent = SequentialAgent(
    name = "StoryPipeline",
    sub_agents=[initial_writer_agent, story_refinement_loop]
)

runner = InMemoryRunner(agent=root_agent)

async def main():
    response = await runner.run_debug(
        "Write a short story on the 'Frankenstein'"
    )

asyncio.run(main())
