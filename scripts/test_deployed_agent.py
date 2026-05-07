#!/usr/bin/env python3
"""
Test the deployed Smart Offer Modeler on Vertex AI Agent Engine.

Usage:
    python scripts/test_deployed_agent.py

Reads the resource name from scripts/agent_engine_resource.txt.
"""
import asyncio
import pathlib
import sys
import vertexai

# Reuse the same env-driven config as the agent.
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from smart_offer_agent.config import GCP_PROJECT as PROJECT, GCP_REGION as LOCATION

RESOURCE_FILE = pathlib.Path(__file__).parent / "agent_engine_resource.txt"


def get_resource_name() -> str:
    if not RESOURCE_FILE.exists():
        print(f"ERROR: {RESOURCE_FILE} not found.")
        print("Deploy the agent first: ./scripts/deploy_agent.sh")
        sys.exit(1)
    return RESOURCE_FILE.read_text().strip()


async def run_test():
    resource_name = get_resource_name()
    print(f"Testing agent: {resource_name}\n")

    vertexai.init(project=PROJECT, location=LOCATION)
    remote_app = vertexai.agent_engines.get(resource_name)

    session = await remote_app.async_create_session(user_id="ta-test-001")
    print(f"Session created: {session['id']}\n")

    turns = [
        (
            "Model an offer for Arjun Sharma as a Senior Software Engineer in "
            "Bengaluru. They have a competing offer of ₹52,00,000 and "
            "we want to propose a base of ₹44,00,000."
        ),
        "What if we proposed ₹46,00,000 instead?",
    ]

    for i, message in enumerate(turns, 1):
        print(f"--- Turn {i} ---")
        print(f"User: {message}")
        print("Agent: ", end="", flush=True)

        async for event in remote_app.async_stream_query(
            user_id="ta-test-001",
            session_id=session["id"],
            message=message,
        ):
            content = event.get("content", {})
            for part in content.get("parts", []):
                if part.get("text"):
                    print(part["text"], end="", flush=True)
        print("\n")


asyncio.run(run_test())
