import json
import sys

try:
    with open('home_automation_agent/integration.evalset.json', 'r') as f:
        data = json.load(f)
    print("JSON is valid")
except json.JSONDecodeError as e:
    print(f"JSON error: {e}")
except Exception as e:
    print(f"Error: {e}")
