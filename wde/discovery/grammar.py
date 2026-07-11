"""Territory generation grammar — combinatorial creative space with compatibility rules.

P6 — diversify concepts without hand-coding full sector families every time.

Axes:
  Métaphore × structure × signature × typography intensity × materiality
  × image treatment × motion × conversion mode
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from wde.discovery.interpret import Interpretation
from wde.discovery.territories import Territory
from wde.discovery.tokens import DesignTokens


@dataclass(frozen=True)
class GrammarAxes:
    metaphor: str
    structure: str
    signature: str
    type_intensity: str
    materiality: str
    image: str
    motion: int
    conversion: str


METAPHORS = (
    "hand-annotated field notebook",
    "front-desk reservation ledger",
    "location scouting reel",
    "precision lab instrument",
    "printed shift runbook",
    "network topology map",
    "bound archive volume",
    "workshop tool bench",
    "theatre cue sheet",
    "tasting-note card deck",
    "museum wall label system",
    "shipping manifest board",
    "score and libretto page",
    "cartographic survey plate",
)

STRUCTURES = (
    "Vertical chapter spine with sticky mono markers",
    "Dense ledger rows: key | status | action",
    "Horizontal sequence frames 01…n",
    "Spec-first table → guarantees → CTA",
    "Numbered procedures with deep TOC",
    "Left rail nodes; main stage is active hop",
    "Index → essays → contact",
    "Tools → process → proof → hire",
    "Cue 1…n sparse dialogue",
    "Layered tasting progression: nose → palate → finish",
    "Wall of labels → focused object → room note",
    "Manifest columns that collapse to a single path",
)

SIGNATURES = (
    "Itinerary rail doubles as nav and progress",
    "CTA is a stamped desk request, not a pill spam",
    "Site advances as edited scenes",
    "Hero is a live metric strip",
    "Page reads as an ops manual chapter",
    "Conversion is the last hop in the path",
    "Index numbers as navigation",
    "Layout as a bench grid of tools",
    "CTA appears only on final cue",
    "Aromatic vocabulary is interactive and filterable",
    "Wall labels expand into object stories",
    "Manifest line becomes the only conversion path",
)

TYPE_INTENSITY = (
    "display serif + mono captions",
    "tracked uppercase mono + restrained sans",
    "wide tracked sans + micro captions",
    "mono metrics + geometric sans claims",
    "serif body prose + mono commands",
    "condensed display + tiny mono labels",
)

MATERIALITY = (
    "paper ivory + ink",
    "near-black hairline brass",
    "cinema black + silver",
    "zinc monochrome + status green",
    "off-white paper + warning red",
    "dark field + cyan edge",
    "warm grey + tool steel",
    "black stage + follow-spot",
)

IMAGES = (
    "tactile photography with margin annotations",
    "minimal keys stamps paper texture",
    "cinematic letterbox stills",
    "schematics only — no lifestyle",
    "none or simple diagrams",
    "abstract nodes only",
    "full-bleed stills with captions",
    "process close-ups",
    "high-contrast stills",
    "macro material photography",
)

CONVERSIONS = (
    "primary CTA in final chapter only",
    "stamped request in ledger action column",
    "last hop of the path",
    "inline reservation inside tasting finish",
    "hire / book after proof section",
    "contact after index essay",
)

MOTIONS = (1, 2, 3, 5, 6, 7, 8)

# Soft compatibility: metaphor family → preferred structure/signature indices
_FAMILY_BIAS: dict[str, tuple[tuple[int, ...], tuple[int, ...]]] = {
    "notebook": ((0, 6, 9), (0, 6, 9)),
    "ledger": ((1, 11), (1, 11)),
    "scouting": ((2, 8), (2, 8)),
    "lab": ((3, 4), (3, 4)),
    "runbook": ((4, 3), (4, 3)),
    "topology": ((5, 3), (5, 3)),
    "archive": ((6, 0), (6, 0)),
    "workshop": ((7, 1), (7, 1)),
    "theatre": ((8, 2), (8, 2)),
    "tasting": ((9, 0), (9, 3)),
    "museum": ((10, 6), (10, 6)),
    "manifest": ((11, 1), (11, 11)),
    "score": ((0, 6), (0, 6)),
    "cartographic": ((0, 11), (0, 11)),
}


def _seed_int(text: str) -> int:
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(h[:12], 16)


def _rng(seed: int) -> callable:
    """Tiny deterministic LCG."""
    state = seed & 0xFFFFFFFF

    def next_int(n: int) -> int:
        nonlocal state
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        return state % max(1, n)

    return next_int


def _family_key(metaphor: str) -> str:
    low = metaphor.lower()
    for k in _FAMILY_BIAS:
        if k in low:
            return k
    return "notebook"


def _compatible(m: str, s: str, img: str, motion: int) -> bool:
    blob = f"{m} {s} {img}".lower()
    if "lab instrument" in blob and ("tasting" in blob or "cue sheet" in blob):
        return False
    if "runbook" in blob and "cinematic letterbox" in blob:
        return False
    if "topology" in blob and "tasting" in blob:
        return False
    if motion >= 7 and "none or simple" in img:
        return False
    if motion <= 2 and "sequence frames" in s.lower() and "cinematic" not in img:
        return False
    return True


def _tokens_for_materiality(mat: str, type_i: str) -> DesignTokens:
    low = mat.lower()
    display = "Fraunces" if "serif" in type_i.lower() else "IBM Plex Sans"
    if any(k in low for k in ("paper", "ivory", "off-white", "warm grey")):
        accent = "#C44C4C" if "red" in low or "warning" in low else "#B8956A"
        if "steel" in low:
            accent = "#6B7280"
        paper = "#F3EEE4" if "ivory" in low or "paper" in low else "#EDE8E1"
        return DesignTokens.light_editorial(paper=paper, accent=accent, display=display)
    accent = "#C4A35A"
    if "green" in low:
        accent = "#5FA657"
    if "cyan" in low:
        accent = "#5B9EA6"
    if "silver" in low:
        accent = "#A8B0B8"
    if "spot" in low:
        accent = "#E8D5A3"
    return DesignTokens.dark_instrument(accent=accent, display=display)


def _axes_distance(a: GrammarAxes, b: GrammarAxes) -> int:
    score = 0
    if a.metaphor != b.metaphor:
        score += 3
    if a.structure != b.structure:
        score += 3
    if a.signature != b.signature:
        score += 2
    if a.motion != b.motion:
        score += 2
    if a.materiality != b.materiality:
        score += 1
    if a.image != b.image:
        score += 1
    if a.conversion != b.conversion:
        score += 1
    if a.type_intensity != b.type_intensity:
        score += 1
    return score


def _sample_axes(rnd, metaphor_idx: int | None = None) -> GrammarAxes | None:
    for _ in range(40):
        mi = metaphor_idx if metaphor_idx is not None else rnd(len(METAPHORS))
        m = METAPHORS[mi % len(METAPHORS)]
        fam = _family_key(m)
        pref_s, pref_sig = _FAMILY_BIAS.get(fam, ((0, 1, 2), (0, 1, 2)))
        if rnd(3) == 0:
            st = STRUCTURES[rnd(len(STRUCTURES))]
            sig = SIGNATURES[rnd(len(SIGNATURES))]
        else:
            st = STRUCTURES[pref_s[rnd(len(pref_s))] % len(STRUCTURES)]
            sig = SIGNATURES[pref_sig[rnd(len(pref_sig))] % len(SIGNATURES)]
        ty = TYPE_INTENSITY[rnd(len(TYPE_INTENSITY))]
        mat = MATERIALITY[rnd(len(MATERIALITY))]
        img = IMAGES[rnd(len(IMAGES))]
        motion = MOTIONS[rnd(len(MOTIONS))]
        conv = CONVERSIONS[rnd(len(CONVERSIONS))]
        if _compatible(m, st, img, motion):
            return GrammarAxes(m, st, sig, ty, mat, img, motion, conv)
    return None


def pick_divergent_triplet(seed: int, min_distance: int = 8) -> list[GrammarAxes]:
    """Sample 3 divergent axis bundles without full cartesian explosion."""
    rnd = _rng(seed)
    # Force three different metaphor families when possible
    family_order = list(range(len(METAPHORS)))
    family_order.sort(key=lambda i: rnd(10_000) + i)
    chosen: list[GrammarAxes] = []
    for mi in family_order:
        if len(chosen) >= 3:
            break
        cand = _sample_axes(rnd, metaphor_idx=mi)
        if cand is None:
            continue
        if all(_axes_distance(cand, c) >= min_distance for c in chosen):
            # also require distinct motion bands when possible
            if chosen and cand.motion in {c.motion for c in chosen} and rnd(2) == 0:
                continue
            chosen.append(cand)
    # Fill with looser threshold
    attempts = 0
    while len(chosen) < 3 and attempts < 200:
        attempts += 1
        cand = _sample_axes(rnd)
        if cand is None:
            continue
        thr = min_distance if len(chosen) < 2 else max(5, min_distance - 3)
        if all(_axes_distance(cand, c) >= thr for c in chosen):
            chosen.append(cand)
    while len(chosen) < 3:
        fallback = _sample_axes(rnd) or GrammarAxes(
            METAPHORS[len(chosen)],
            STRUCTURES[len(chosen)],
            SIGNATURES[len(chosen)],
            TYPE_INTENSITY[0],
            MATERIALITY[len(chosen) % len(MATERIALITY)],
            IMAGES[0],
            (2, 5, 7)[len(chosen)],
            CONVERSIONS[0],
        )
        chosen.append(fallback)
    # Ensure motion divergence
    motions = [c.motion for c in chosen]
    if len(set(motions)) < 2:
        fixed = []
        for i, c in enumerate(chosen):
            fixed.append(
                GrammarAxes(
                    c.metaphor,
                    c.structure,
                    c.signature,
                    c.type_intensity,
                    c.materiality,
                    c.image,
                    (2, 5, 7)[i],
                    c.conversion,
                )
            )
        chosen = fixed
    return chosen[:3]


def axes_to_territory(
    axes: GrammarAxes, tid: str, name_hint: str, interp: Interpretation
) -> Territory:
    tokens = _tokens_for_materiality(axes.materiality, axes.type_intensity)
    anti = [
        "3 equal feature cards",
        "blue→purple hero gradient",
        "fake trusted-by logo wall",
        "generic modern premium chrome",
        "defaulting every brand to supercar chrome references",
    ]
    return Territory(
        id=tid,
        name=name_hint,
        metaphor=axes.metaphor,
        structure=axes.structure,
        primary_interaction=f"{axes.signature}; conversion: {axes.conversion}",
        typography=axes.type_intensity,
        image_treatment=axes.image,
        motion_level=axes.motion,
        palette_role=axes.materiality,
        signature_move=axes.signature,
        anti_references=anti,
        hero=f"{axes.metaphor} — {axes.signature}",
        archetype_hint=f"grammar:{axes.materiality[:24]}",
        tokens=tokens,
    )


def generate_from_grammar(interp: Interpretation, *, count: int = 3) -> list[Territory]:
    """Build ``count`` divergent territories from the grammar."""
    seed = _seed_int(interp.raw_request + "|" + interp.sector_key + "|" + interp.subject)
    triplet = pick_divergent_triplet(seed)
    names = ("Grammar α", "Grammar β", "Grammar γ")
    ids = ("A", "B", "C")
    out: list[Territory] = []
    for i in range(min(count, 3)):
        out.append(axes_to_territory(triplet[i], ids[i], names[i], interp))
    return out


def structural_distance_territories(a: Territory, b: Territory) -> int:
    ax = GrammarAxes(
        metaphor=a.metaphor,
        structure=a.structure,
        signature=a.signature_move,
        type_intensity=a.typography,
        materiality=a.palette_role,
        image=a.image_treatment,
        motion=a.motion_level,
        conversion=a.primary_interaction,
    )
    bx = GrammarAxes(
        metaphor=b.metaphor,
        structure=b.structure,
        signature=b.signature_move,
        type_intensity=b.typography,
        materiality=b.palette_role,
        image=b.image_treatment,
        motion=b.motion_level,
        conversion=b.primary_interaction,
    )
    return _axes_distance(ax, bx)


def diversity_report(runs: list[list[Territory]]) -> dict:
    metaphors: dict[str, int] = {}
    palettes: dict[str, int] = {}
    for territories in runs:
        for t in territories:
            metaphors[t.metaphor] = metaphors.get(t.metaphor, 0) + 1
            palettes[t.palette_role] = palettes.get(t.palette_role, 0) + 1
    total_m = max(1, sum(metaphors.values()))
    total_p = max(1, sum(palettes.values()))
    return {
        "metaphor_freq": metaphors,
        "palette_freq": palettes,
        "max_metaphor_share": max(metaphors.values(), default=0) / total_m,
        "max_palette_share": max(palettes.values(), default=0) / total_p,
        "unique_metaphors": len(metaphors),
        "unique_palettes": len(palettes),
    }


def asserts_no_universal_bugatti(territories: list[Territory]) -> bool:
    """Bugatti must not appear as the owned metaphor/signature (anti-universal crutch)."""
    for t in territories:
        blob = f"{t.metaphor} {t.signature_move} {t.name}".lower()
        if "bugatti" in blob:
            return False
    return True
