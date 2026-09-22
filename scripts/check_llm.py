"""Check in 10 seconds if an Azure OpenAI endpoint + key still work.

Usage (from the project root, with backend/.env filled in):
    python scripts/check_llm.py

It sends one tiny request and explains the result in plain words.
"""
import os
import sys
from pathlib import Path

import requests

env_file = Path(__file__).resolve().parent.parent / "backend" / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5.4-mini")
api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")

if not endpoint or not api_key:
    sys.exit("Missing AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY in backend/.env")

#Builds the full address of your model:
url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
print(f"Calling: {url}")

try:
    resp = requests.post(
        url,
        headers={"api-key": api_key, "Content-Type": "application/json"},
        json={"messages": [{"role": "user", "content": "Say OK"}]},# Sends one tiny message, "Say OK", so it costs almost nothing.
        timeout=20,
    )
except requests.ConnectionError:
    sys.exit("❌ Can't connect. The resource name is wrong or the resource was deleted.")
except requests.Timeout:
    sys.exit("❌ Timeout. Try again, or check your network.")

meanings = {
    200: "✅ It works! Endpoint, key and deployment are all fine.",
    401: "❌ 401: the API key is wrong or was rotated.",
    403: "❌ 403: access denied (network rules or permissions on the resource).",
    404: "❌ 404: the deployment name or api-version is wrong, or the deployment was deleted.",
    410: "❌ 410: this model version is retired. Ask for a newer deployment.",
    429: "⚠️ 429: rate limited, but the setup itself works.",
}
#Reads the answer code and explains it in simple words:
print(meanings.get(resp.status_code, f"❌ Unexpected status {resp.status_code}"))
if resp.status_code == 200:
    print("Model answered:", resp.json()["choices"][0]["message"]["content"])
else:
    print("Details:", resp.text[:300])
