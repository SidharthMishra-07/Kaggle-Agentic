
import subprocess
import requests
import time
import os

print("🚀 Starting Product Catalog Agent server...")

server_process = subprocess.Popen(
    [
        "uvicorn",
        "product_catalog_agent:app",  # Module:app format
        "--host", "localhost",
        "--port", "8001",
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env={**os.environ},
)

print("   Waiting for server to be ready...")
max_attempts = 30
for attempt in range(max_attempts):
    try:
        response = requests.get("http://localhost:8001/.well-known/agent-card.json", timeout=1)
        if response.status_code == 200:
            print("\n✅ Product Catalog Agent server is running!")
            print("   URL: http://localhost:8001")
            break
    except requests.exceptions.RequestException:
        time.sleep(5)
        print(".", end="", flush=True)
else:
    print("\n⚠️Server may not be ready yet. Check manually.")
