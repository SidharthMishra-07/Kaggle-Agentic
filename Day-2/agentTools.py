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


retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

#Get Payment Method
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


#Get exchange rate
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

currency_agent = LlmAgent(
    name="currency_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""You are a smart currency conversion assistant.

    For currency conversion requests:
    1. Use `get_fee_for_payment_method()` to find transaction fees
    2. Use `get_exchange_rate()` to get currency conversion rates
    3. Check the "status" field in each tool's response for errors
    4. Calculate the final amount after fees based on the output from `get_fee_for_payment_method` and `get_exchange_rate` methods and provide a clear breakdown.
    5. First, state the final converted amount.
        Then, explain how you got that result by showing the intermediate amounts. Your explanation must include: the fee percentage and its
        value in the original currency, the amount remaining after the fee, and the exchange rate used for the final conversion.

    If any tool returns status "error", explain the issue to the user clearly.
    """,
    tools=[FunctionTool(get_fee_for_payment_method), FunctionTool(get_exchange_rate)],
)

print("✅ Currency agent created with custom function tools")

currency_runner = InMemoryRunner(agent=currency_agent)

async def main():
    response = await currency_runner.run_debug(
        "I want to convert 500 USD into INR using my Platinum credit card. How much will i receive?"
    )

asyncio.run(main()) 