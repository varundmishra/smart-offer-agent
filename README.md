# BRD 2: Smart Offer Modeler (A-209)

A pro-code reasoning agent built with Google ADK that assists Talent Acquisition in structuring competitive job offers. Uses Gemini 2.5 Pro to enforce compensation rules and generate data-backed offer justifications.

**Client (fictional, for demo purposes):** Cymbal HR
**GCP Project:** `your-project-id` | **Region:** `us-central1` | **Model:** `gemini-2.5-pro`

> **Naming convention:** all customer-facing artifacts (system prompt, demo scripts, generated content) reference the fictional company **Cymbal HR**. Do not introduce any real client name into prompts, READMEs, or seed data.

---

## Prerequisites

- Python 3.11+
- `gcloud` CLI installed and authenticated
- Access to `your-project-id` GCP project with roles: `roles/bigquery.admin`, `roles/aiplatform.user`

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project your-project-id
```

---

## Project Structure

```
brd2/
├── smart_offer_agent/          ← ADK module (must contain __init__.py + agent.py)
│   ├── __init__.py
│   ├── agent.py                ← root_agent defined here
│   ├── tools/
│   │   ├── market_tool.py
│   │   ├── peers_tool.py
│   │   ├── bands_tool.py
│   │   └── offer_calculator.py
│   ├── logic/
│   │   ├── compensation_rules.py
│   │   └── compa_ratio.py
│   └── prompts/
│       └── system_prompt.txt
├── data/
│   ├── schemas/                ← BigQuery JSON schema files
│   └── seed/                   ← CSV seed data
│       ├── market_benchmarks.csv
│       ├── internal_peers.csv
│       └── salary_bands.csv
├── scripts/
│   ├── generate_seed_data.py   ← generates India-specific CSVs into data/seed/
│   ├── create_dataset.sh
│   ├── seed_bigquery.py
│   └── deploy_agent.sh
├── tests/
├── infra/terraform/
├── requirements.txt
└── .env
```

---

## Step 1: Install Dependencies

```bash
cd brd2
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install google-adk google-cloud-bigquery google-cloud-aiplatform
pip install -r requirements.txt
```

---

## Step 2: Configure Environment

Create `brd2/smart_offer_agent/.env`:

```bash
# For Vertex AI (use this for production and Agent Engine deployment)
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

> **Note:** When running locally with `adk web`, ADK reads the `.env` file automatically from the agent module directory.

---

## Step 3: Set Up BigQuery Data Layer

### 3a. Create Dataset and Tables

```bash
chmod +x scripts/create_dataset.sh
./scripts/create_dataset.sh
```

This script runs:
```bash
bq mk --dataset --location=US your-project-id:smart_offer_ds
bq mk --table your-project-id:smart_offer_ds.market_benchmarks data/schemas/market_benchmarks.json
bq mk --table your-project-id:smart_offer_ds.internal_peers data/schemas/internal_peers.json
bq mk --table your-project-id:smart_offer_ds.salary_bands data/schemas/salary_bands.json
```

### 3b. Generate Seed Data

```bash
python3 scripts/generate_seed_data.py
```

This generates India-specific CSV files in `data/seed/`:
- `market_benchmarks.csv` — 80 rows (10 roles × 8 Indian metros), INR, Mercer_India_2026
- `salary_bands.csv` — 80 rows (10 roles × 8 Indian metros), INR, effective_year 2026
- `internal_peers.csv` — 1,000 rows with Indian names and INR salaries

### 3c. Load into BigQuery

```bash
python3 scripts/seed_bigquery.py
```

Verify:
```bash
bq query --use_legacy_sql=false \
  "SELECT role_title, COUNT(*) as count FROM your-project-id.smart_offer_ds.internal_peers GROUP BY role_title ORDER BY count DESC"
```

Expected: 1,000 rows across 10 roles.

---

## Step 4: Run Locally with `adk web`

> **Important:** Run from the `brd2/` directory (the parent of `smart_offer_agent/`). ADK discovers agent modules in the current directory.

**Without telemetry:**
```bash
cd brd2
adk web
```

**With telemetry (traces → Cloud Trace, logs → Cloud Logging):**
```bash
cd brd2
adk web --otel_to_cloud
```

Open your browser at **http://localhost:8000**

In the top-left dropdown, select **`smart_offer_agent`**.

### Test Prompts

**Full offer scenario (all entities provided):**
```
Model an offer for Arjun Sharma as a Senior Software Engineer in Bengaluru.
They have a competing offer of ₹52,00,000 and we want to propose a base of ₹44,00,000.
```

**Cap rule test (proposed base exceeds highest internal peer):**
```
I need to offer Priya Mehta a Senior Software Engineer role in Bengaluru.
The competing offer is ₹62,00,000 and I want to offer a base of ₹60,00,000.
```

**Different role and metro:**
```
Model an offer for Rohan Iyer as a Product Manager in Mumbai.
Competing offer is ₹70,00,000 and we want to propose a base of ₹58,00,000.
```

**What to verify in the Events tab:**
- `get_market_benchmarks`, `get_internal_peers`, and `get_salary_band` fire first (can be parallel)
- `calculate_offer` fires after all three complete
- Response contains: Structured Offer Breakdown, Equity Analysis Summary, Executive Approval Justification
- If proposed base > `max_peer_base`, the capped base in the output must equal `max_peer_base`

---

## Step 5: Run Tests

```bash
# Unit tests (no GCP credentials needed)
pytest tests/unit/ -v

# Integration tests (requires BQ credentials, live your-project-id project)
RUN_INTEGRATION=true pytest tests/integration/ -v

# E2E tests (requires live agent + BQ)
pytest tests/e2e/ -v
```

---

## Step 6: Deploy to Vertex AI Agent Engine

> **Official docs reference:** https://google.github.io/adk-docs/deploy/agent-engine/

### 6a. Authenticate (if not already done)
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project your-project-id
```

### 6b. Enable Required APIs
```bash
gcloud services enable aiplatform.googleapis.com --project=your-project-id
gcloud services enable bigquery.googleapis.com --project=your-project-id
```

### 6c. Deploy

Run from the `brd2/` directory:

```bash
adk deploy agent_engine \
    --project=your-project-id \
    --region=us-central1 \
    --display_name="Smart Offer Modeler A-209" \
    smart_offer_agent
```

> ADK packages your agent code and dependencies and deploys them to Vertex AI Agent Engine (Reasoning Engine). This takes 3–5 minutes.

**Save the resource name printed on completion:**
```
Deployed: projects/your-project-id/locations/us-central1/reasoningEngines/XXXXXXXXXXXXXXXXX
```

Save this ID to `scripts/agent_engine_resource.txt`.

---

## Step 7: Test the Deployed Agent

```python
# test_deployed.py — run from brd2/ directory
import asyncio
import vertexai

PROJECT_ID = "your-project-id"
LOCATION = "us-central1"
RESOURCE_NAME = "projects/your-project-id/locations/us-central1/reasoningEngines/XXXXXXXXXXXXXXXXX"

vertexai.init(project=PROJECT_ID, location=LOCATION)

async def test_agent():
    remote_app = vertexai.agent_engines.get(RESOURCE_NAME)

    # Create a session
    session = await remote_app.async_create_session(user_id="test-user-001")
    print(f"Session created: {session['id']}")

    # Send a test message
    async for event in remote_app.async_stream_query(
        user_id="test-user-001",
        session_id=session["id"],
        message="Model an offer for Arjun Sharma as a Senior Software Engineer in Bengaluru. Competing offer is ₹52,00,000, proposed base is ₹44,00,000.",
    ):
        if event.get("content"):
            for part in event["content"].get("parts", []):
                if part.get("text"):
                    print(part["text"])

asyncio.run(test_agent())
```

Run it:
```bash
python test_deployed.py
```

**Alternatively, test via REST:**
```bash
RESOURCE_ID="XXXXXXXXXXXXXXXXX"

# Create session
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/your-project-id/locations/us-central1/reasoningEngines/${RESOURCE_ID}:query" \
  -d '{"class_method": "async_create_session", "input": {"user_id": "u_001"}}'

# Stream query (replace SESSION_ID with value from above)
curl \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/your-project-id/locations/us-central1/reasoningEngines/${RESOURCE_ID}:streamQuery?alt=sse" \
  -d '{
    "class_method": "async_stream_query",
    "input": {
      "user_id": "u_001",
      "session_id": "SESSION_ID",
      "message": "Model an offer for Arjun Sharma as a Senior Software Engineer in Bengaluru. Competing offer ₹52,00,000, proposed base ₹44,00,000."
    }
  }'
```

---

## Step 8: Register with Gemini Enterprise

> **Note:** The official ADK documentation does not document a programmatic API for Gemini Enterprise registration. The steps below reflect the Google Workspace Admin Console flow as of early 2025 — confirm with your Google Workspace admin.

1. Go to **Google Workspace Admin Console** → Apps → Gemini for Workspace → Extensions
2. Click **"Add Extension"** → **"Agent Engine"**
3. Enter the Agent Engine resource name from Step 6:
   ```
   projects/your-project-id/locations/us-central1/reasoningEngines/XXXXXXXXXXXXXXXXX
   ```
4. Set the agent display name: `"Smart Offer Modeler"`
5. Set the description: `"Structures competitive job offers using internal pay equity data and market benchmarks. Enforces compensation rules and generates executive approval justifications."`
6. Assign access to the relevant Google Workspace groups (e.g., `talent-acquisition@cymbal-hr.com`)
7. Save and wait for propagation (~5 minutes)

**Verify:** Open Gemini for Workspace in Gmail or Google Chat, type `@Smart Offer Modeler` and send a test offer modeling request.

---

## Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| `adk web` shows no agents | Running from wrong directory | Run from `brd2/` (parent of `smart_offer_agent/`) |
| BQ `403 Access Denied` | Missing IAM role | Grant `roles/bigquery.dataViewer` to your user/SA |
| `adk deploy` fails with packaging error | Missing `__init__.py` | Ensure `smart_offer_agent/__init__.py` exists |
| Tool returns empty dict | Role/location not in seed data | Check CSV — use exact strings e.g. `"Senior Software Engineer"`, `"Bengaluru"` |
| Compa-ratio calculation wrong | `band_midpoint` is 0 | Verify salary_bands table has row for the role+location+year |

---

## IAM Summary

| Principal | Role | Scope |
|---|---|---|
| Developer (local `adk web`) | `roles/bigquery.dataViewer`, `roles/bigquery.jobUser` | Project `your-project-id` |
| Agent Engine SA (Gemini Enterprise / deployed) | `roles/bigquery.dataViewer`, `roles/bigquery.jobUser`, `roles/aiplatform.user` | Project `your-project-id` |

> **Which account is the Agent Engine SA?**
> When deployed to Vertex AI Agent Engine (including when accessed via Gemini Enterprise), the agent runs as a Google-managed service account — **not your user account**.
> Grant permissions using:
> ```bash
> PROJECT_NUMBER=$(gcloud projects describe your-project-id --format="value(projectNumber)")
>
> gcloud projects add-iam-policy-binding your-project-id \
>   --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
>   --role="roles/bigquery.dataViewer"
>
> gcloud projects add-iam-policy-binding your-project-id \
>   --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
>   --role="roles/bigquery.jobUser"
> ```
