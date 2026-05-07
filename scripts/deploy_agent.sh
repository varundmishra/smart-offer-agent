#!/usr/bin/env bash
set -euo pipefail

# Load .env from the agent module so we share config with the Python code.
ENV_FILE="$(dirname "$0")/../smart_offer_agent/.env"
[[ -f "$ENV_FILE" ]] && set -a && source "$ENV_FILE" && set +a

PROJECT="${GCP_PROJECT:-${GOOGLE_CLOUD_PROJECT:-}}"
REGION="${GCP_REGION:-${GOOGLE_CLOUD_LOCATION:-us-central1}}"
DISPLAY_NAME="${AGENT_DISPLAY_NAME:-Smart Offer Modeler A-209}"
AGENT_MODULE="smart_offer_agent"
RESOURCE_FILE="$(dirname "$0")/agent_engine_resource.txt"

# Run from the brd2/ directory
SCRIPT_DIR="$(dirname "$0")"
cd "${SCRIPT_DIR}/.."

echo "Deploying ${AGENT_MODULE} to Vertex AI Agent Engine ..."
echo "  Project:  ${PROJECT}"
echo "  Region:   ${REGION}"
echo "  Module:   ${AGENT_MODULE}"
echo ""

OUTPUT=$(adk deploy agent_engine \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --display_name="${DISPLAY_NAME}" \
  --trace_to_cloud \
  --env_file "${AGENT_MODULE}/opentelemetry.env" \
  "${AGENT_MODULE}" 2>&1)

echo "${OUTPUT}"

RESOURCE_NAME=$(echo "${OUTPUT}" | grep -oE 'projects/[^ ]+/reasoningEngines/[0-9]+' | tail -1)

if [ -z "${RESOURCE_NAME}" ]; then
  echo ""
  echo "Could not auto-extract resource name. Copy it manually from the output above"
  echo "and save it to: ${RESOURCE_FILE}"
else
  echo "${RESOURCE_NAME}" > "${RESOURCE_FILE}"
  echo ""
  echo "Resource name saved to: ${RESOURCE_FILE}"
  echo "  ${RESOURCE_NAME}"
fi
