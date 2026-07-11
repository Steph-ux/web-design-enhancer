"""Generate three structurally divergent creative territories (not palette swaps)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from wde.discovery.interpret import Interpretation
from wde.discovery.tokens import DesignTokens

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
    # Structured tokens — compiler source of truth for DESIGN.md
    tokens: DesignTokens = field(default_factory=lambda: DesignTokens.dark_instrument())

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d

    def resolved_tokens(self) -> DesignTokens:
        """Prefer explicit tokens; else derive from palette_role + typography."""
        # Heuristic: if tokens still look like default dark but palette says paper, re-derive
        if self.tokens and self.tokens.background:
            # Explicit structured tokens always win
            return self.tokens
        return DesignTokens.from_palette_role(self.palette_role, self.typography)


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
            tokens=DesignTokens.light_editorial(
                paper="#F3EEE4",
                ink="#1A1A1A",
                accent="#C4A35A",
                display="Fraunces",
            ),
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
            tokens=DesignTokens.dark_instrument(accent="#C4A35A", display="IBM Plex Sans"),
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
            tokens=DesignTokens.dark_instrument(bg="#0B0B0C", accent="#A8B0B8", display="IBM Plex Sans"),
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
            tokens=DesignTokens.dark_instrument(accent="#5FA657", display="IBM Plex Sans"),
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
            tokens=DesignTokens.light_editorial(
                paper="#F3EEE4",
                ink="#1A1A1A",
                accent="#C44C4C",
                display="Fraunces",
            ),
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
            tokens=DesignTokens.dark_instrument(accent="#5B9EA6", display="IBM Plex Sans"),
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
            tokens=DesignTokens.light_editorial(paper="#F3EEE4", display="Fraunces"),
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
            tokens=DesignTokens.light_editorial(
                paper="#EDE8E1",
                accent="#6B7280",
                display="IBM Plex Sans",
            ),
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
            tokens=DesignTokens.dark_instrument(accent="#E8D5A3", display="IBM Plex Sans"),
        ),
    ]


def generate_territories(
    interp: Interpretation,
    synthesis: Any | None = None,
    *,
    use_grammar: bool | None = None,
) -> list[Territory]:
    """Return exactly three divergent territories for the interpretation.

    Optional ``synthesis`` (ResearchSynthesis) can bias metaphor notes / anti-refs
    without collapsing structural divergence.

    ``use_grammar``:
      - True → always combinatorial grammar (P6)
      - False → curated sector families only
      - None → grammar for unknown sectors; curated for agency/hospitality/saas
    """
    key = interp.sector_key
    if use_grammar is True:
        from wde.discovery.grammar import generate_from_grammar

        territories = generate_from_grammar(interp)
    elif use_grammar is False:
        if key in {"agency", "hospitality"}:
            territories = _agency_hospitality_set(interp)
        elif key == "saas":
            territories = _saas_set(interp)
        else:
            territories = _generic_set(interp)
    else:
        # default: curated when we have strong families, else grammar
        if key in {"agency", "hospitality"}:
            territories = _agency_hospitality_set(interp)
        elif key == "saas":
            territories = _saas_set(interp)
        else:
            from wde.discovery.grammar import generate_from_grammar

            territories = generate_from_grammar(interp)

    if synthesis is not None:
        territories = _apply_synthesis(territories, synthesis)
    return territories


def _apply_synthesis(territories: list[Territory], synthesis: Any) -> list[Territory]:
    """Fold research findings into anti-references and signature notes."""
    anti_extra: list[str] = []
    for f in getattr(synthesis, "anti_references", []) or []:
        val = getattr(f, "statement", None) or (f if isinstance(f, str) else str(f))
        if val:
            anti_extra.append(str(val)[:120])
    principles: list[str] = []
    for f in getattr(synthesis, "visual_principles", []) or []:
        val = getattr(f, "statement", None) or (f if isinstance(f, str) else str(f))
        if val:
            principles.append(str(val)[:100])

    out: list[Territory] = []
    for i, t in enumerate(territories):
        anti = list(t.anti_references)
        for a in anti_extra[:3]:
            if a not in anti:
                anti.append(a)
        hero = t.hero
        if principles and i == 0:
            hero = f"{hero} · research: {principles[0]}"
        out.append(
            Territory(
                id=t.id,
                name=t.name,
                metaphor=t.metaphor,
                structure=t.structure,
                primary_interaction=t.primary_interaction,
                typography=t.typography,
                image_treatment=t.image_treatment,
                motion_level=t.motion_level,
                palette_role=t.palette_role,
                signature_move=t.signature_move,
                anti_references=anti[:8],
                hero=hero,
                archetype_hint=t.archetype_hint,
                tokens=t.tokens,
            )
        )
    return out


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
