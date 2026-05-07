"""
E2E tests for the Smart Offer Modeler against the deployed Vertex AI Agent Engine.
Requires the agent to be deployed and agent_engine_resource.txt to be populated.

Run with:
    pytest tests/e2e/ -v
"""
import asyncio
import pathlib
import sys
import pytest
import vertexai

# Reuse the agent's env-driven config so e2e tests follow whatever GCP project
# the rest of the system is pointed at (your-project-id by default; override via env).
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))
from smart_offer_agent.config import GCP_PROJECT as PROJECT, GCP_REGION as LOCATION

RESOURCE_FILE = pathlib.Path(__file__).parent.parent.parent / "scripts" / "agent_engine_resource.txt"


@pytest.fixture(scope="module")
def resource_name():
    if not RESOURCE_FILE.exists():
        pytest.skip("agent_engine_resource.txt not found — deploy the agent first")
    name = RESOURCE_FILE.read_text().strip()
    if not name:
        pytest.skip("agent_engine_resource.txt is empty")
    return name


@pytest.fixture(scope="module")
def remote_app(resource_name):
    vertexai.init(project=PROJECT, location=LOCATION)
    return vertexai.agent_engines.get(resource_name)


def collect_response(remote_app, session_id: str, user_id: str, message: str) -> str:
    parts = []
    async def _run():
        async for event in remote_app.async_stream_query(
            user_id=user_id,
            session_id=session_id,
            message=message,
        ):
            for part in event.get("content", {}).get("parts", []):
                if part.get("text"):
                    parts.append(part["text"])
    asyncio.run(_run())
    return "".join(parts)


class TestFullOfferScenario:
    """FR1: All data retrieved; FR2: cap rule; FR3: compa-ratio; output has all three documents."""

    def test_standard_offer_bengaluru(self, remote_app):
        async def _setup():
            return await remote_app.async_create_session(user_id="e2e-001")
        session = asyncio.run(_setup())

        response = collect_response(
            remote_app, session["id"], "e2e-001",
            "Model an offer for Arjun Sharma as a Senior Software Engineer in Bengaluru. "
            "They have a competing offer of ₹52,00,000 and we want to propose a base of ₹44,00,000.",
        )

        assert "Arjun Sharma" in response
        assert "Structured Offer Breakdown" in response or "Offer Breakdown" in response
        assert "Compa" in response
        assert "Justification" in response or "Business Case" in response

    def test_cap_applied_when_proposed_exceeds_peer(self, remote_app):
        async def _setup():
            return await remote_app.async_create_session(user_id="e2e-002")
        session = asyncio.run(_setup())

        response = collect_response(
            remote_app, session["id"], "e2e-002",
            "I need to offer Priya Mehta a Senior Software Engineer role in Bengaluru. "
            "The competing offer is ₹62,00,000 and I want to offer a base of ₹60,00,000.",
        )

        # The capped base should be less than the proposed ₹60,00,000
        assert "Cap Applied" in response or "cap" in response.lower()

    def test_multi_turn_adjustment(self, remote_app):
        async def _setup():
            return await remote_app.async_create_session(user_id="e2e-003")
        session = asyncio.run(_setup())

        # Turn 1 — initial offer
        collect_response(
            remote_app, session["id"], "e2e-003",
            "Model an offer for Rohan Iyer as a Product Manager in Mumbai. "
            "Competing offer is ₹70,00,000 and we want to propose a base of ₹58,00,000.",
        )

        # Turn 2 — adjust proposed base
        response2 = collect_response(
            remote_app, session["id"], "e2e-003",
            "What if we proposed ₹62,00,000 instead?",
        )

        assert "62" in response2 or "6200000" in response2.replace(",", "")
