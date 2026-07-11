"""WDE Creative Discovery — interpret → research → synthesize → diverge → select → compile → traces."""

from wde.discovery.grammar import generate_from_grammar
from wde.discovery.orchestrator import DiscoveryResult, run_discovery
from wde.discovery.synthesis import ResearchSynthesis, synthesize_research
from wde.discovery.tokens import DesignTokens
from wde.discovery.traces import run_all_traces

__all__ = [
    "run_discovery",
    "DiscoveryResult",
    "ResearchSynthesis",
    "synthesize_research",
    "DesignTokens",
    "generate_from_grammar",
    "run_all_traces",
]

from wde.discovery.orchestrator import run_discovery

__all__ = ["run_discovery"]
