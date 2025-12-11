import os
import asyncio
import json
import uuid
from dotenv import load_dotenv

from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner, InMemoryRunner
from google.adk.sessions import InMemorySessionService

from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams, StdioServerParameters 
# from mcp import StdioServerParameters

from google.adk.apps.app import App, ResumabilityConfig
from google.adk.tools.function_tool import FunctionTool

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("🔑 GOOGLE_API_KEY not found in .env file")


retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

# MCP integration with Everything Server
mcp_image_server = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "--", "@modelcontextprotocol/server-everything"],
            tool_filter=["getTinyImage"]
        ),
        timeout=30
    )
)

print("✅ MCP Tool created")


# *** Behind the scenes:

# 1.Server Launch: ADK runs npx -y @modelcontextprotocol/server-everything
# 2.Handshake: Establishes stdio communication channel
# 3.Tool Discovery: Server tells ADK: "I provide getTinyImage" functionality
# 4.Integration: Tools appear in agent's tool list automatically
# 5.Execution: When agent calls getTinyImage(), ADK forwards to MCP server
# 6.Response: Server result is returned to agent seamlessly

# Why This Matters: You get instant access to tools without writing integration code!

# 2.3: Extending to Other MCP Servers
# The same pattern works for any MCP server - only the connection_params change. Here are some examples:

#Kaggle MCP Server
kaggle_mcp_server = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=[
                '-y',
                'mcp-remote',
                'https://www.kaggle.com/mcp'
            ]
        ),
        timeout=30
    )
)

#Github MCP Server
# github_mcp_server = McpToolset(
#     connection_params=StreamableHTTPServerParams(
#         url="https://api.githubcopilot.com/mcp/",
#         headers={
#             "Authorization": f"Bearer {GITHUB_TOKEN}",
#             "X-MCP-Toolsets": "all",
#             "X-MCP-Readonly": "true"
#         },
#     ),
# )


#Add MCP tool to agent
image_agent = LlmAgent(
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    name="image_agent",
    instruction="Use the MCP Tool to generate images for user queries",
    tools=[mcp_image_server]
)

runner = InMemoryRunner(agent=image_agent)

async def main():
    response = await runner.run_debug(
        "Provide a sample tiny image", 
        verbose=True
    )

asyncio.run(main()) 