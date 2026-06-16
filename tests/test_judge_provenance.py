"""
tests/test_judge_provenance.py
Recommendation #5B — fix the judge-bias problem.

The model that GENERATED the design is usually the same one scoring its
screenshots, so a self-review is structurally inflated. These tests cover:
  - reviewer_kind classification (self/agent, independent/api, human, unknown)
  - the self-judge provenance discount in calibrate_verdict
  - independent / human verdicts trusted without discount
  - backward compatibility (no reviewer field -> no SCORE penalty)
  - the adversarial art-director bar in the prompt
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

_AR = Path(__file__).parent.parent / "scripts" / "aesthetic_review.py"


def _load():
    spec = importlib.util.spec_from_file_location("ar_prov", _AR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _verdict(score, reviewer=None, fixes=None):
    v = {
        "overall_score": score,
        "reads_as": "human",
        "dimensions": {k: {"score": score, "note": "n"} for k in
                       ["first_impression", "visual_hierarchy", "whitespace_balance",
                        "typography_craft", "colour_harmony", "finish_consistency", "human_vs_ai"]},
        "top_fixes": fixes if fixes is not None else ["fix one aaaa", "fix two bbbb"],
    }
    if reviewer is not None:
        v["reviewer"] = reviewer
    return v


# --- reviewer_kind classification ------------------------------------------

class TestReviewerKind:
    def test_self_and_agent_map_to_self(self):
        c = _load()
        assert c.reviewer_kind({"reviewer": "self"}) == "self"
        assert c.reviewer_kind({"reviewer": "agent"}) == "self"

    def test_independent_and_api_map_to_independent(self):
        c = _load()
        assert c.reviewer_kind({"reviewer": "independent"}) == "independent"
        assert c.reviewer_kind({"reviewer": "api"}) == "independent"

    def test_human(self):
        c = _load()
        assert c.reviewer_kind({"reviewer": "human"}) == "human"

    def test_missing_is_unknown(self):
        c = _load()
        assert c.reviewer_kind({}) == "unknown"

    def test_case_insensitive(self):
        c = _load()
        assert c.reviewer_kind({"reviewer": "SELF"}) == "self"
        assert c.reviewer_kind({"reviewer": "Independent"}) == "independent"


# --- self-judge discount ----------------------------------------------------

class TestSelfJudgeDiscount:
    def test_self_review_is_discounted(self):
        c = _load()
        eff, flags = c.calibrate_verdict(_verdict(80, reviewer="self"), 60, 75)
        assert eff == 80 - c.SELF_JUDGE_DISCOUNT
        assert any(f.startswith("SELF-JUDGED") for f in flags)

    def test_self_review_can_drop_below_pass(self):
        # A self-flattered "shippable" 80 should fall below the 75 pass mark.
        c = _load()
        eff, _ = c.calibrate_verdict(_verdict(80, reviewer="self"), 60, 75)
        assert eff < 75  # 80 - 8 = 72

    def test_independent_review_not_discounted(self):
        c = _load()
        eff, flags = c.calibrate_verdict(_verdict(80, reviewer="independent"), 60, 75)
        assert eff == 80
        assert not any(f.startswith("SELF-JUDGED") for f in flags)

    def test_human_review_not_discounted(self):
        c = _load()
        eff, flags = c.calibrate_verdict(_verdict(80, reviewer="human"), 60, 75)
        assert eff == 80
        assert not any(f.startswith("SELF-JUDGED") for f in flags)

    def test_missing_reviewer_no_score_penalty(self):
        # Backward compatibility: legacy verdicts keep their score; only an
        # advisory PROVENANCE UNKNOWN flag is added.
        c = _load()
        eff, flags = c.calibrate_verdict(_verdict(80), 60, 75)
        assert eff == 80
        assert any(f.startswith("PROVENANCE UNKNOWN") for f in flags)
        assert not any(f.startswith("SELF-JUDGED") for f in flags)

    def test_discount_stacks_after_inflation_guard(self):
        # A self-judged near-perfect verdict eats BOTH penalties.
        c = _load()
        eff, flags = c.calibrate_verdict(
            _verdict(98, reviewer="self", fixes=["a aaaaaaa", "b bbbbbbb", "c ccccccc"]), 60, 75)
        # 98 - 10 (inflation, >=3 fixes) - 8 (self) = 80
        assert eff == 80
        assert any(f.startswith("INFLATION GUARD") for f in flags)
        assert any(f.startswith("SELF-JUDGED") for f in flags)

    def test_discount_never_below_zero(self):
        c = _load()
        eff, _ = c.calibrate_verdict(_verdict(3, reviewer="self"), 60, 75)
        assert eff == 0


# --- adversarial prompt -----------------------------------------------------

class TestAdversarialPrompt:
    def test_prompt_has_art_director_test(self):
        c = _load()
        p = c.build_prompt("§3 Luxury", ["desktop", "mobile"])
        assert "ART-DIRECTOR TEST" in p
        assert "inspiration folder" in p

    def test_prompt_caps_clean_but_unmemorable(self):
        c = _load()
        p = c.build_prompt(None, ["desktop"])
        assert "FLOOR" in p
        assert "memorable" in p

    def test_schema_requests_memorable_idea(self):
        c = _load()
        p = c.build_prompt(None, ["desktop"])
        assert "memorable_idea" in p


# --- CLI integration --------------------------------------------------------

class TestCLIReviewer:
    def _run(self, verdict, extra=None):
        f = tempfile.mktemp(suffix=".json")
        Path(f).write_text(json.dumps(verdict), encoding="utf-8")
        args = [sys.executable, str(_AR), "--verdict", f, "--json"] + (extra or [])
        r = subprocess.run(args, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        return r.returncode, json.loads(r.stdout)

    def test_reviewer_flag_overrides_verdict_field(self):
        # An 80 self-review passes only because --reviewer human overrides it.
        code_self, out_self = self._run(_verdict(80, reviewer="self"))
        code_human, out_human = self._run(_verdict(80, reviewer="self"), ["--reviewer", "human"])
        assert out_self["effective_score"] == 72  # discounted
        assert out_human["effective_score"] == 80  # trusted
        assert code_self == 1   # below pass 75 -> polish
        assert code_human == 0  # pass

    def test_agent_manifest_declares_self_reviewer(self):
        d = tempfile.mkdtemp()
        # minimal 1x1 png
        import base64
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
        (Path(d) / "desktop.png").write_bytes(png)
        r = subprocess.run(
            [sys.executable, str(_AR), "--screenshots", d, "--archetype", "§6 Technical"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        m = json.loads(r.stdout)
        assert m["declared_reviewer"] == "self"
        assert "reviewer" in m["verdict_schema"]
