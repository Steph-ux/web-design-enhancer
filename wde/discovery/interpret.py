"""Request interpreter — explicit creative hypotheses, never fake user facts."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CreativeHypothesis:
    field: str
    value: str
    confidence: str = "assumed"  # assumed | inferred | user_stated
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Interpretation:
    raw_request: str
    subject: str
    audience: str
    primary_action: str
    emotion: str
    page_kind: str
    sector_key: str
    creative_risk: int  # 1-10
    hypotheses: list[CreativeHypothesis] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    search_queries: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


# Lightweight sector cues → concrete default framing (creative choice, not user fact)
_SECTOR_MAP: list[tuple[re.Pattern[str], dict[str, str]]] = [
    (
        re.compile(r"hotel|hospitalit|h[oô]tel|concierge|resort", re.I),
        {
            "subject": "independent boutique hospitality brand / hotel group",
            "audience": "discerning leisure travellers and independent hoteliers",
            "primary_action": "request a consultation / book a stay inquiry",
            "emotion": "quiet arrival — like opening a leather guest ledger at dusk",
            "page_kind": "marketing landing + inquiry",
            "sector_key": "hospitality",
        },
    ),
    (
        re.compile(r"agenc|studio|branding|strat[eé]gie|creative", re.I),
        {
            "subject": "brand strategy agency for independent hotels",
            "audience": "hotel owners and marketing directors seeking premium positioning",
            "primary_action": "book a strategy consultation",
            "emotion": "confident restraint of a private atelier",
            "page_kind": "agency portfolio landing",
            "sector_key": "agency",
        },
    ),
    (
        re.compile(r"saas|software|api|b2b|dashboard|fintech", re.I),
        {
            "subject": "B2B product / technical SaaS",
            "audience": "operators and technical buyers",
            "primary_action": "start trial or book a demo",
            "emotion": "precision instrument on a dark bench",
            "page_kind": "product landing",
            "sector_key": "saas",
        },
    ),
    (
        re.compile(r"portfolio|designer|developer|cv|freelance", re.I),
        {
            "subject": "personal creative / developer portfolio",
            "audience": "hiring managers and collaborators",
            "primary_action": "send an inquiry",
            "emotion": "focused studio — one craft, no carnival",
            "page_kind": "portfolio",
            "sector_key": "portfolio",
        },
    ),
    (
        re.compile(r"e-?com|shop|store|boutique|retail", re.I),
        {
            "subject": "specialty retail / digital goods storefront",
            "audience": "buyers comparing quality over volume",
            "primary_action": "purchase or start checkout",
            "emotion": "inventory board — exact, unsentimental",
            "page_kind": "storefront",
            "sector_key": "commerce",
        },
    ),
]

_DEFAULT = {
    "subject": "brand strategy agency for independent hotels",
    "audience": "independent hotel owners seeking a distinct brand voice",
    "primary_action": "request a consultation",
    "emotion": "quiet confidence of a private front desk after hours",
    "page_kind": "agency marketing landing",
    "sector_key": "agency",
}


def _risk_from_request(text: str) -> int:
    t = text.lower()
    if any(w in t for w in ("bold", "experimental", "brutal", "wild", "audacieux")):
        return 8
    if any(w in t for w in ("safe", "corporate", "classic", "conserv")):
        return 3
    if any(w in t for w in ("premium", "luxury", "luxe", "moderne", "modern")):
        return 5
    return 6


def interpret_request(raw: str) -> Interpretation:
    """Turn a vague prompt into a structured interpretation with labeled assumptions."""
    text = (raw or "").strip() or "a modern premium website for an agency"
    matched = None
    for pat, framing in _SECTOR_MAP:
        if pat.search(text):
            matched = framing
            break
    framing = dict(matched or _DEFAULT)

    # If request is extremely vague ("modern premium site"), force explicit agency-hotel default
    vague = bool(
        re.search(r"moderne|modern|premium|beau|nice|clean|pro", text, re.I)
        and not matched
        and len(text.split()) < 12
    )
    if vague:
        framing = dict(_DEFAULT)

    risk = _risk_from_request(text)
    hyps: list[CreativeHypothesis] = []
    for field, value in framing.items():
        if field == "sector_key":
            continue
        hyps.append(
            CreativeHypothesis(
                field=field,
                value=value,
                confidence="assumed" if (vague or not matched) else "inferred",
                rationale=(
                    "Explicit creative hypothesis because the user request did not specify this — "
                    "not a claimed user fact."
                    if vague or not matched
                    else "Inferred from keywords in the user request."
                ),
            )
        )
    hyps.append(
        CreativeHypothesis(
            field="creative_risk",
            value=str(risk),
            confidence="assumed",
            rationale="Default risk dial for discovery; raise/lower if user specifies.",
        )
    )

    open_q = [
        "Confirm subject vertical if different from the creative hypothesis.",
        "Confirm primary conversion action (consult / book / buy / subscribe).",
        "Any brand assets, photography, or tone-of-voice documents available?",
    ]

    sector = framing["sector_key"]
    queries = {
        "sector": f"{framing['subject']} brand website conversion journey content types",
        "visual": f"{sector} editorial monochrome premium web design composition typography",
        "anti_reference": f"generic {sector} agency template cliches card grid blue gradient",
        "cross_domain": f"{sector} non-web inspiration luggage tags topographic maps guest ledgers",
        "promax": f"{sector} premium monochrome landing editorial dense typography",
    }

    return Interpretation(
        raw_request=text,
        subject=framing["subject"],
        audience=framing["audience"],
        primary_action=framing["primary_action"],
        emotion=framing["emotion"],
        page_kind=framing["page_kind"],
        sector_key=sector,
        creative_risk=risk,
        hypotheses=hyps,
        open_questions=open_q,
        search_queries=queries,
    )


def interpretation_seed(interp: Interpretation) -> int:
    """Stable seed for deterministic territory generation."""
    h = hashlib.sha256(interp.raw_request.encode("utf-8")).hexdigest()
    return int(h[:8], 16)
