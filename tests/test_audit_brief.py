"""Tests for scripts/audit_brief.py — Creative-Brief quality scorer."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "audit_brief.py"

SHARP = """# CREATIVE-BRIEF.md

## Emotional Intent
When someone lands they must feel like walking into a Zurich architect studio at
midnight, cold concrete and a single warm lamp, expensive restraint.

## The One Unexpected Thing
The lead story has no image at all; the headline itself, set huge, is the only
artwork on the page and that is the whole bet.

## Hero Dimension
- [x] Typography
- [ ] Colour

## The Broken Rule
We ignore the 8px grid on the H1 because the violent jump from 120px to 16px body
IS the broadsheet personality; soften it and it becomes a blog.

## Design Read
A long-form journalism front page for general readers, editorial language.

## Design Dials
- VARIANCE: **9**
- MOTION: **2**
- DENSITY: **6**

## The Cross-Domain Steal
The non-software discipline I am stealing from: print editorial, the front page of
a broadsheet newspaper. The specific move: vertical hairline column rules splitting
the page into unequal columns with a dominating lead above the fold.
"""

FILLER = """# CREATIVE-BRIEF.md

## Emotional Intent
Professional and modern, a clean elegant experience.

## The One Unexpected Thing
A sleek hero like Stripe with a nice gradient.

## Hero Dimension
- [x] Typography
- [x] Colour

## The Broken Rule
We will ignore some grid rules.

## Design Read
A modern website for users.

## Design Dials
- VARIANCE: 8

## The Cross-Domain Steal
Stealing from another SaaS landing page, the app dashboard layout.
"""


# --- French fixtures: a sharp brief and filler, to lock bilingual lexicons ----

SHARP_FR = """# CREATIVE-BRIEF.md

## Emotional Intent
Quand quelqu'un arrive il doit se sentir dans l'arrière-salle d'une usine de
pressage de vinyle à 3h du matin, l'odeur de PVC chaud, une seule ampoule nue
au-dessus de la presse, comme attendre que la matrice refroidisse.

## The One Unexpected Thing
Le catalogue n'a aucune pochette visible au départ ; chaque sortie est seulement
sa forme d'onde gravée, énorme, en pleine largeur, et c'est tout le pari.

## Hero Dimension
- [x] Motion
- [ ] Typography
- [ ] Colour

## The Broken Rule
On ignore le défilement vertical sage : la page défile horizontalement comme un
sillon de vinyle, parce que ce mouvement EST l'identité du label.

## Design Read
Un site de catalogue pour un label techno underground, langage brut.

## Design Dials
- VARIANCE: **8**
- MOTION: **9**
- DENSITY: **3**

## The Cross-Domain Steal
La discipline non-logicielle que je vole : la signalétique des clubs de Berlin et
le pressage de vinyle. Le mouvement précis : la lecture en spirale d'un sillon,
de l'extérieur vers un point central unique.
"""

FILLER_FR = """# CREATIVE-BRIEF.md

## Emotional Intent
Une expérience moderne et professionnelle, épurée et élégante.

## The One Unexpected Thing
Un hero immersif comme Spotify avec un beau dégradé.

## Hero Dimension
- [x] Typography
- [x] Colour

## The Broken Rule
On va ignorer certaines règles de grille.

## Design Read
Un site web moderne pour un label de musique.

## Design Dials
- VARIANCE: 7

## The Cross-Domain Steal
On s'inspire d'une autre landing page SaaS et du tableau de bord d'une appli.
"""


# --- Mixed FR/EN + accent-stripped fixtures (risk #3: unpredictable scoring) --

# A sharp brief whose two languages are interleaved in the SAME sections AND whose
# French is typed WITHOUT accents (signaletique, gravee, defilement) — the exact
# shape that scored B4 6/22 before accent-folding.
MIXED = """# CREATIVE-BRIEF.md

## Emotional Intent
When someone lands here it should feel like the back room of an usine de pressage
de vinyle at 3am, the smell of hot PVC, une seule ampoule nue above the press,
comme attendre que the matrix cools down.

## The One Unexpected Thing
The catalogue has no visible pochette at first; each release is only its waveform
gravee, enormous, full-width, et c est tout le pari.

## Hero Dimension
- [x] Motion
- [ ] Typography
- [ ] Colour

## The Broken Rule
We ignore le defilement vertical sage: the page scrolls horizontally like a sillon
de vinyle, because that movement IS the label identity.

## Design Read
A catalogue site pour un label techno underground, raw language.

## Design Dials
- VARIANCE: **8**
- MOTION: **9**
- DENSITY: **3**

## The Cross-Domain Steal
The non-software discipline I steal: la signaletique des clubs de Berlin and vinyl
pressing. The precise move: la lecture en spirale d un sillon, from outside toward
a single central point.
"""


def run(tmp_path, text, *args):
    p = tmp_path / "CREATIVE-BRIEF.md"
    p.write_text(text, encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), "--brief", str(p), *args],
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def test_sharp_brief_scores_high(tmp_path):
    r = run(tmp_path, SHARP)
    assert r.returncode == 0
    assert "SHARP" in r.stdout


def test_filler_brief_blocked(tmp_path):
    r = run(tmp_path, FILLER)
    assert r.returncode == 1
    assert "BLOCKED" in r.stdout


def test_missing_file_exit_2():
    r = subprocess.run([sys.executable, str(SCRIPT), "--brief", "/nope/none.md"],
                       capture_output=True, text=True)
    assert r.returncode == 2


def test_software_steal_scores_zero(tmp_path):
    r = run(tmp_path, FILLER, "--json")
    data = json.loads(r.stdout)
    b4 = next(d for d in data["dimensions"] if d["id"] == "B4")
    assert b4["points"] == 0


def test_nonsoftware_label_not_false_flagged(tmp_path):
    # "non-software discipline" must NOT trip the software blacklist.
    r = run(tmp_path, SHARP, "--json")
    data = json.loads(r.stdout)
    b4 = next(d for d in data["dimensions"] if d["id"] == "B4")
    assert b4["points"] == b4["max"]


def test_bold_markdown_dials_parsed(tmp_path):
    # **9** / **2** / **6** must parse, and the extreme (9) must be rewarded.
    r = run(tmp_path, SHARP, "--json")
    data = json.loads(r.stdout)
    b5 = next(d for d in data["dimensions"] if d["id"] == "B5")
    assert b5["points"] == b5["max"]


def test_two_hero_dims_penalised(tmp_path):
    r = run(tmp_path, FILLER, "--json")
    data = json.loads(r.stdout)
    b6 = next(d for d in data["dimensions"] if d["id"] == "B6")
    assert b6["points"] < b6["max"]


# --- Bilingual (French) coverage ---------------------------------------------

def test_sharp_french_brief_passes(tmp_path):
    # A genuinely sharp brief written in French must clear the floor, not be
    # penalised for its language (regression: B4 scored 6/22 before bilingual lexicons).
    r = run(tmp_path, SHARP_FR)
    assert r.returncode == 0
    assert "SHARP" in r.stdout


def test_french_nonsoftware_steal_full_credit(tmp_path):
    # "signalétique" + "pressage de vinyle" are non-software disciplines -> full B4.
    r = run(tmp_path, SHARP_FR, "--json")
    data = json.loads(r.stdout)
    b4 = next(d for d in data["dimensions"] if d["id"] == "B4")
    assert b4["points"] == b4["max"]


def test_french_filler_brief_blocked(tmp_path):
    # "moderne / professionnelle / épurée" + "appli/SaaS" steal must be caught as filler.
    r = run(tmp_path, FILLER_FR)
    assert r.returncode == 1
    assert "BLOCKED" in r.stdout


def test_french_software_steal_penalised(tmp_path):
    # French software reference ("autre landing SaaS", "tableau de bord d'une appli")
    # must NOT earn full B4 credit.
    r = run(tmp_path, FILLER_FR, "--json")
    data = json.loads(r.stdout)
    b4 = next(d for d in data["dimensions"] if d["id"] == "B4")
    assert b4["points"] < b4["max"]


def test_french_vague_terms_penalise_b1(tmp_path):
    # "moderne / épurée / élégante" are vague -> B1 below max.
    r = run(tmp_path, FILLER_FR, "--json")
    data = json.loads(r.stdout)
    b1 = next(d for d in data["dimensions"] if d["id"] == "B1")
    assert b1["points"] < b1["max"]


# Rare craft / artisanal disciplines must earn full B4 credit too — not just the
# common ones (signalétique, pressage). This is the "unknown lexical field" risk.
@pytest.mark.parametrize("discipline", [
    "la lutherie",        # FR rare craft
    "la ferronnerie",     # FR rare craft
    "blacksmithing",      # EN rare craft
    "bookbinding",        # EN rare craft
])
def test_rare_craft_steal_full_credit(tmp_path, discipline):
    brief = SHARP_FR.replace(
        "La discipline non-logicielle que je vole : la signalétique des clubs de Berlin et\n"
        "le pressage de vinyle.",
        f"La discipline non-logicielle que je vole : {discipline}.",
    )
    r = run(tmp_path, brief, "--json")
    data = json.loads(r.stdout)
    b4 = next(d for d in data["dimensions"] if d["id"] == "B4")
    assert b4["points"] == b4["max"]


# --- Mixed FR/EN + accent-stripped (risk #3) ---------------------------------

def test_mixed_fr_en_brief_passes(tmp_path):
    # A sharp brief interleaving FR/EN in the same sections, with the French typed
    # WITHOUT accents, must still clear PASS — language mixing is not a defect.
    r = run(tmp_path, MIXED)
    assert r.returncode == 0
    assert "SHARP" in r.stdout


def test_mixed_brief_accentless_steal_full_credit(tmp_path):
    # "signaletique" (no accent) + "vinyl pressing" must earn full B4 — accent
    # folding makes the accented lexicon match the unaccented input (regression:
    # this scored B4 6/22 before fold()).
    r = run(tmp_path, MIXED, "--json")
    data = json.loads(r.stdout)
    b4 = next(d for d in data["dimensions"] if d["id"] == "B4")
    assert b4["points"] == b4["max"]


def test_accentless_french_filler_still_blocked(tmp_path):
    # Negative: stripping accents must NOT let filler sneak through. An accentless
    # version of the FR filler ("moderne / professionnelle / epuree") stays blocked.
    accentless = FILLER_FR.replace("épurée", "epuree").replace("élégante", "elegante")
    r = run(tmp_path, accentless)
    assert r.returncode == 1
    assert "BLOCKED" in r.stdout


def test_accentless_vague_terms_still_penalise_b1(tmp_path):
    # The fold must cut BOTH ways: accent-stripped buzzwords ("epuree", "elegante")
    # must still be caught as vague, or filler would score full B1 by dropping accents.
    accentless = FILLER_FR.replace("épurée", "epuree").replace("élégante", "elegante")
    r = run(tmp_path, accentless, "--json")
    data = json.loads(r.stdout)
    b1 = next(d for d in data["dimensions"] if d["id"] == "B1")
    assert b1["points"] < b1["max"]
