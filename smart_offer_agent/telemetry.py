"""
Observability setup for Smart Offer Agent.

Tracing:  ADK handles OpenTelemetry tracing internally via --trace_to_cloud (deploy)
          or --otel_to_cloud (local adk web). Do not set up a custom TracerProvider.

Logging:  Call setup_logging() once at startup to route Python logging to Cloud Logging
          with the correct ReasoningEngine resource labels, per:
          https://docs.cloud.google.com/agent-builder/agent-engine/manage/logging

Usage:
    from smart_offer_agent.telemetry import setup_logging
    setup_logging()
"""
import logging
import os

from smart_offer_agent.config import GCP_PROJECT as PROJECT_ID
from smart_offer_agent.config import GCP_REGION as LOCATION

LOG_NAME = os.environ.get("LOG_NAME", "smart-offer-agent")


def setup_logging() -> None:
    """
    Route Python's standard logging to Cloud Logging with ReasoningEngine resource labels.
    Safe to call at module import time — falls back gracefully if google-cloud-logging
    is not installed or credentials are unavailable (e.g. local dev without --otel_to_cloud).
    """
    try:
        import google.cloud.logging
        from google.cloud.logging import Resource

        client = google.cloud.logging.Client(project=PROJECT_ID)
        client.setup_logging(
            name=LOG_NAME,
            resource=Resource(
                type="aiplatform.googleapis.com/ReasoningEngine",
                labels={
                    "location": LOCATION,
                    "resource_container": PROJECT_ID,
                    # Set automatically by Agent Engine at runtime; empty string locally
                    "reasoning_engine_id": os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID", ""),
                },
            ),
        )
        logging.getLogger(__name__).info(
            "Cloud Logging configured (project=%s, log=%s)", PROJECT_ID, LOG_NAME
        )
    except Exception as exc:
        # Do not block agent startup if logging setup fails
        logging.basicConfig(level=logging.INFO)
        logging.getLogger(__name__).warning(
            "Cloud Logging setup skipped (%s) — falling back to stdout", exc
        )
