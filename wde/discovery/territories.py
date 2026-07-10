"""Generate three structurally divergent creative territories (not palette swaps)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from wde.discovery.interpret import Interpretation


CRITIQUE_CRITERIA = (
    "relevance",
    "distinction",
    "clarity",
    "feasibility",
    "responsive",
    "conversion",
    "signature",
    "sobriety",
)


@dataclass
class Territory:
    id: str
    name: str
    metaphor: str
    structure: str
    primary_interaction: str
    typography: str
    image_treatment: str
    motion_level: int  # 1-10
    palette_role: str
    signature_move: str
    anti_references: list[str] = field(default_factory=list)
    hero: str = ""
    archetype_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _agency_hospitality_set(interp: Interpretation) -> list[Territory]:
    return [
        Territory(
            id="A",
            name="Carnet de voyage éditorial",
            metaphor="Hand-annotated travel notebook / topographic notes",
            structure="Vertical itinerary spine: Discover → Approach → Cases → Contact",
            primary_interaction="Scroll as journey; chapter markers as sticky mono labels",
            typography="Display serif for place names + mono for coordinates / captions",
            image_treatment="Tactile photography with margin annotations; no stock smiles",
            motion_level=3,
            palette_role="Paper ivory + ink black + one map-ochre accent only for route",
            signature_move="Itinerary rail doubles as navigation and narrative progress",
            anti_references=[
                "3-column service cards",
                "blue→purple hero gradient",
                "logo wall trusted-by",
            ],
            hero="Full-bleed quiet photo + oversized place-name type, no CTA pill spam",
            archetype_hint="§2 Editorial / §3 Luxury restraint",
        ),
        Territory(
            id="B",
            name="Registre de réception",
            metaphor="Hotel front-desk reservation ledger / key rack",
            structure="Dense ledger rows: Date | Guest intent | Status | Action",
            primary_interaction="Row expand / key-tag filters; institutional precision",
            typography="Tracked uppercase mono headers + restrained sans body",
            image_treatment="Minimal; keys, stamps, paper texture as system not decoration",
            motion_level=2,
            palette_role="Near-black surfaces, hairline borders, single brass status mark",
            signature_move="Navigation as ledger columns; CTA is a stamped 'Request desk'",
            anti_references=[
                "floating glassmorphism cards",
                "animated blob backgrounds",
                "emoji section markers",
            ],
            hero="Monumental wordmark + single brass rule + live 'desk open' instrument",
            archetype_hint="§6 Technical monochrome × hospitality austerity",
        ),
        Territory(
            id="C",
            name="Film de lieu",
            metaphor="Location scouting reel / sequence montage",
            structure="Horizontal sequences: Frame 01… Frame 04; sparse copy per beat",
            primary_interaction="Sequence scrub / chapter jump; optional ambient silence",
            typography="Wide tracked sans titles; micro captions under frames",
            image_treatment="Cinematic crops, letterbox framing, no collage clutter",
            motion_level=7,
            palette_role="Cinema black, silver highlights, one cool practical light accent",
            signature_move="Site advances as edited scenes, not stacked marketing sections",
            anti_references=[
                "autoplay loud video hero with stock voiceover",
                "equal feature tiles under video",
                "neon SaaS glow",
            ],
            hero="Single wide still as 'frame 01' with scene slate numbers",
            archetype_hint="§3 Luxury restraint + disciplined motion",
        ),
    ]


def _saas_set(interp: Interpretation) -> list[Territory]:
    return [
        Territory(
            id="A",
            name="Instrument panel",
            metaphor="Precision lab instrument / oscilloscope",
            structure="Spec-first: Problem → Guarantees table → API surface → CTA",
            primary_interaction="Tabular densify; copy-to-clipboard specs",
            typography="Mono for metrics + geometric sans for claims",
            image_treatment="Schematics / wire diagrams only — no lifestyle",
            motion_level=2,
            palette_role="Zinc monochrome + one semantic status green",
            signature_move="Hero is a live metric strip, not a gradient blob",
            anti_references=["3 feature cards", "purple glow", "fake testimonials"],
            hero="Huge mono product name + single amber focus line",
            archetype_hint="§6 Technical monochrome",
        ),
        Territory(
            id="B",
            name="Operator handbook",
            metaphor="Printed runbook / shift handbook",
            structure="Numbered procedures; deep-linked sections",
            primary_interaction="In-page TOC as chapter list",
            typography="Serif body for prose + mono for commands",
            image_treatment="None or simple diagrams",
            motion_level=1,
            palette_role="Off-white paper, black ink, red for warnings only",
            signature_move="Marketing page reads as an ops manual chapter",
            anti_references=["bento grid", "3D abstract shapes", "gradient text"],
            hero="Chapter title '01 — Start here' at editorial scale",
            archetype_hint="§2 Editorial",
        ),
        Territory(
            id="C",
            name="Signal path",
            metaphor="Network topology / packet path",
            structure="Left rail nodes; main stage is the active hop",
            primary_interaction="Click node to reveal hop detail",
            typography="Condensed display + tiny mono labels",
            image_treatment="Abstract nodes only",
            motion_level=5,
            palette_role="Dark field, cyan edge only on active hop",
            signature_move="Conversion is the last hop in the path, not a sticky bar",
            anti_references=["hero illustration of people with laptops", "rainbow charts"],
            hero="Animated path that settles into a quiet static graph",
            archetype_hint="§6 / §8 data calm",
        ),
    ]


def _generic_set(interp: Interpretation) -> list[Territory]:
    subj = interp.subject
    return [
        Territory(
            id="A",
            name="Editorial archive",
            metaphor="Bound volume / index of works",
            structure="Index → essays → contact",
            primary_interaction="Long-form scroll with pull quotes",
            typography="Display serif + quiet sans",
            image_treatment="Full-bleed stills with captions",
            motion_level=2,
            palette_role="Ink and paper",
            signature_move="Index numbers as navigation",
            anti_references=["card grids", "default indigo"],
            hero=f"Oversized title for {subj}",
            archetype_hint="§2 Editorial",
        ),
        Territory(
            id="B",
            name="Workshop bench",
            metaphor="Work surface with tools laid out",
            structure="Tools → process → proof → hire",
            primary_interaction="Hover tool reveals craft note",
            typography="Mono labels + sans body",
            image_treatment="Process close-ups",
            motion_level=3,
            palette_role="Warm grey + one tool-steel accent",
            signature_move="Layout as a bench grid, not marketing sections",
            anti_references=["floating cards", "soft purple gradients"],
            hero="Tool silhouette as the only ornament",
            archetype_hint="§6 Technical",
        ),
        Territory(
            id="C",
            name="Stage sequence",
            metaphor="Theatre cue sheet",
            structure="Cue 1…n; sparse dialogue",
            primary_interaction="Next cue advances narrative",
            typography="Wide tracked titles",
            image_treatment="High-contrast stills",
            motion_level=6,
            palette_role="Black stage, single follow-spot accent",
            signature_move="CTA appears only on final cue",
            anti_references=["endless scroll of features", "emoji bullets"],
            hero="Cue light and silence",
            archetype_hint="§3 Luxury / motion",
        ),
    ]


def generate_territories(interp: Interpretation) -> list[Territory]:
    """Return exactly three divergent territories for the interpretation."""
    key = interp.sector_key
    if key in {"agency", "hospitality"}:
        return _agency_hospitality_set(interp)
    if key == "saas":
        return _saas_set(interp)
    return _generic_set(interp)


def territories_are_structurally_divergent(territories: list[Territory]) -> bool:
    """Guard: not three palette swaps — metaphors, structure, interaction must differ."""
    if len(territories) != 3:
        return False
    metaphors = {t.metaphor for t in territories}
    structures = {t.structure for t in territories}
    interactions = {t.primary_interaction for t in territories}
    motions = {t.motion_level for t in territories}
    return (
        len(metaphors) == 3
        and len(structures) == 3
        and len(interactions) == 3
        and len(motions) >= 2
    )
