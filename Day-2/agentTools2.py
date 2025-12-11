import os
import asyncio
import json
from dotenv import load_dotenv

from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search, AgentTool, ToolContext, FunctionTool
from google.adk.code_executors import BuiltInCodeExecutor


# Load environment variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("🔑 GOOGLE_API_KEY not found in .env file")

#Get exchange rates
try:
    with open('exchangeRate.json', 'r') as file:
        exRate = json.load(file)
except FileNotFoundError:
    print("Error: 'exchangeRate.json' not found.")
except json.JSONDecodeError:
    print("Error: Failed to decode JSON from the file.")

#Helper Function
def show_python_code_and_result(response):
    for i in range(len(response)):
        if((response[i].content.parts) and (response[i].content.parts[0])
            and (response[i].content.parts[0].function_response)
            and (response[i].content.parts[0].function_response.response)
        ):
            response_code = response[i].content.parts[0].function_response.response
            if "result" in response_code and response_code["result"] != "```":
                if "tool_code" in response_code["result"]:
                    print(
                        "Generated Python Code >> ",
                        response_code["result"].replace("tool_code", ""),
                    )
                else:
                    print("Generated Python Response >> ", response_code["result"])

print("✅ Helper functions defined.")


retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)


def get_fee_for_payment_method(method: str) -> dict:
    """
    YOUR TASK IS TO DETERMINE THE FEE WITH RESPECT TO THE METHOD PROVIDED

    ARGS:
        method: The name of the payment method, The method has to be descriptive
                eg: "bank transfer", "platinum credit card"
    
    Returns: A dict with status and fee info
        success: {"status" : "success", "fee_percentage" : 0.02}
        error: {"status": "error", "error_message": "Payment method not found"}
    """

    fee_database={
        "platinum credit card" : "0.02",
        "gold debit card" : "0.035",
        "bank transfer" : "0.01",
    }

    fee = fee_database.get(method.lower())

    if fee is not None:
        return {"status" : "success", "fee_percentage" : fee}
    else:
        return {
            "status": "error", 
            "error_message": f"Payment method '{method}' not found"
            }
    
print("✅ Fee lookup function created")


def get_exchange_rate(base_currency: str, target_currency: str) -> dict:
    """Looks up and returns the exchange rate between two currencies.

    Args:
        base_currency: The ISO 4217 currency code of the currency you
                       are converting from (e.g., "USD").
        target_currency: The ISO 4217 currency code of the currency you
                         are converting to (e.g., "EUR").

    Returns:
        Dictionary with status and rate information.
        Success: {"status": "success", "rate": 0.93}
        Error: {"status": "error", "error_message": "Unsupported currency pair"}
    """
    rate_database = { 
        "usd": {
            "eur": 0.93,  
            "jpy": 157.50,  
            "inr": 83.58  
        }
    }   

    base = base_currency.lower()
    target = target_currency.lower()

    rate = rate_database.get(base, {}).get(target)
    if rate is not None:
        return {"status": "success", "rate": rate}
    else:
        return {
            "status": "error", 
            "error_message": f"Unsupported currency pair: {base_currency}/{target_currency}"
        }
    
print("✅ Exchange rate function created")


#Agent Tool
calculation_agent = LlmAgent(
    name = "CalculationAgent",
    model = Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction= """You are a specialized calculator that ONLY responds with Python code. You are forbidden from providing any text, explanations, or conversational responses.
    Your task is to take a request for a calculation and translate it into a single block of Python code that calculates the answer.
    
    **RULES:**
    1.  Your output MUST be ONLY a Python code block.
    2.  Do NOT write any text before or after the code block.
    3.  The Python code MUST calculate the result.
    4.  The Python code MUST print the final result to stdout.
    5.  You are PROHIBITED from performing the calculation yourself. Your only job is to generate the code that will perform the calculation.
   
    Failure to follow these rules will result in an error.

    """,
    code_executor=BuiltInCodeExecutor()
)


enhanced_currency_agent = LlmAgent(
    name="Enhanced_currency_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""You are a smart currency conversion assistant. You must strictly follow these steps and use the available tools.

    For currency conversion requests:
    1. Use `get_fee_for_payment_method()` to find transaction fees
    2. Use `get_exchange_rate()` to get currency conversion rates
    3. Error Check: After each tool call, you must check the "status" field in the response. If the status is "error", you must stop and clearly explain the issue to the user.
    4. Calculate Final Amount (CRITICAL): You are strictly prohibited from performing any arithmetic calculations yourself. You must use the calculation_agent tool to generate Python code that calculates the final converted amount. This 
    code will use the fee information from step 1 and the exchange rate from step 2.
    5. Provide Detailed Breakdown: In your summary, you must:
       * State the final converted amount.
       * Explain how the result was calculated, including:
           * The fee percentage and the fee amount in the original currency.
           * The amount remaining after deducting the fee.
           * The exchange rate applied.
    """,

    tools=[FunctionTool(get_fee_for_payment_method), FunctionTool(get_exchange_rate), AgentTool(agent=calculation_agent)]
)

print("✅ Enhanced currency agent created")

currency_runner = InMemoryRunner(agent=enhanced_currency_agent)

async def main():
    response = await currency_runner.run_debug(
        "I want to convert 1002 USD into INR using a Bank Transfer. How much will i receive?"
    )

asyncio.run(main()) 