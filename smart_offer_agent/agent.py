import pathlib
from google.adk.agents import Agent

from .tools.market_tool import get_market_benchmarks
from .tools.peers_tool import get_internal_peers
from .tools.bands_tool import get_salary_band
from .tools.offer_calculator import calculate_offer

_PROMPT_PATH = pathlib.Path(__file__).parent / "prompts" / "system_prompt.txt"
_SYSTEM_PROMPT = _PROMPT_PATH.read_text()

root_agent = Agent(
    name="smart_offer_agent",
    model="gemini-2.5-flash",
    description=(
        "Structures competitive, policy-compliant job offers for Talent Acquisition. "
        "Enforces internal pay equity rules and generates offer breakdowns with "
        "executive justifications."
    ),
    instruction=_SYSTEM_PROMPT,
    tools=[
        get_market_benchmarks,
        get_internal_peers,
        get_salary_band,
        calculate_offer,
    ],
)
