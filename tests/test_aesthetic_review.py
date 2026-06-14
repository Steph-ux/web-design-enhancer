"""
tests/test_aesthetic_review.py
Tests for the vision-model aesthetic reviewer (aesthetic_review.py).
All network-free: request assembly, response parsing, thresholds, image
encoding, and the rubric contract.
"""
import base64
import json
import tempfile
from pathlib import Path

import pytest
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import aesthetic_review as ar

# A 1x1 transparent PNG.
_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def _shots_dir(names=("mobile", "desktop")) -> Path:
    tmp = Path(tempfile.mkdtemp())
    for n in names:
        (tmp / f"{n}.png").write_bytes(_PNG)
    return tmp


# ─── Screenshot collection ───────────────────────────────────────────────────

class TestCollect:
    def test_collects_pngs_sorted(self):
        d = _shots_dir(("desktop", "mobile", "wide"))
        shots = ar.collect_screenshots(d)
        assert [n for n, _ in shots] == ["desktop", "mobile", "wide"]

    def test_missing_dir_raises(self):
        with pytest.raises(FileNotFoundError):
            ar.collect_screenshots(Path("/no/such/dir/xyz"))

    def test_empty_dir_raises(self):
        d = Path(tempfile.mkdtemp())
        with pytest.raises(FileNotFoundError):
            ar.collect_screenshots(d)

    def test_encode_image_roundtrips(self):
        d = _shots_dir(("mobile",))
        enc = ar.encode_image(d / "mobile.png")
        assert base64.b64decode(enc) == _PNG


# ─── Prompt / rubric ─────────────────────────────────────────────────────────

class TestPrompt:
    def test_prompt_mentions_breakpoints_and_archetype(self):
        p = ar.build_prompt("§3 Luxury", ["mobile", "desktop"])
        assert "mobile" in p and "desktop" in p
        assert "§3 Luxury" in p

    def test_prompt_without_archetype(self):
        p = ar.build_prompt(None, ["desktop"])
        assert "No archetype was declared" in p

    def test_rubric_has_seven_dimensions(self):
        assert len(ar.RUBRIC_DIMENSIONS) == 7
        keys = {k for k, _ in ar.RUBRIC_DIMENSIONS}
        assert "human_vs_ai" in keys and "first_impression" in keys


# ─── Payload assembly ────────────────────────────────────────────────────────

class TestPayloads:
    def test_openai_payload_shape(self):
        shots = ar.collect_screenshots(_shots_dir(("mobile", "desktop")))
        pl = ar.build_openai_payload("gpt-4o", "PROMPT", shots)
        assert pl["model"] == "gpt-4o"
        content = pl["messages"][0]["content"]
        images = [c for c in content if c["type"] == "image_url"]
        assert len(images) == 2
        assert images[0]["image_url"]["url"].startswith("data:image/png;base64,")

    def test_anthropic_payload_shape(self):
        shots = ar.collect_screenshots(_shots_dir(("mobile", "desktop")))
        pl = ar.build_anthropic_payload("claude-3-5-sonnet-latest", "PROMPT", shots)
        content = pl["messages"][0]["content"]
        images = [c for c in content if c["type"] == "image"]
        assert len(images) == 2
        assert images[0]["source"]["type"] == "base64"
        assert images[0]["source"]["media_type"] == "image/png"


# ─── Response extraction + parsing ───────────────────────────────────────────

class TestParsing:
    def test_extract_openai(self):
        resp = {"choices": [{"message": {"content": "hello"}}]}
        assert ar.extract_text_openai(resp) == "hello"

    def test_extract_anthropic(self):
        resp = {"content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]}
        assert ar.extract_text_anthropic(resp) == "ab"

    def test_parse_plain_json(self):
        v = ar.parse_verdict('{"overall_score": 82, "verdict": "nice"}')
        assert v["overall_score"] == 82

    def test_parse_code_fenced_json(self):
        text = "```json\n{\"overall_score\": 70, \"reads_as\": \"human\"}\n```"
        v = ar.parse_verdict(text)
        assert v["overall_score"] == 70
        assert v["reads_as"] == "human"

    def test_parse_json_with_prose_around(self):
        text = "Here is my review:\n{\"overall_score\": 55}\nHope that helps."
        assert ar.parse_verdict(text)["overall_score"] == 55

    def test_parse_missing_score_raises(self):
        with pytest.raises(ValueError):
            ar.parse_verdict('{"verdict": "no score here"}')

    def test_parse_no_json_raises(self):
        with pytest.raises(ValueError):
            ar.parse_verdict("totally not json")


# ─── Thresholds / exit codes ─────────────────────────────────────────────────

class TestThresholds:
    def test_pass(self):
        assert ar.exit_code_for(80, 60, 75) == 0

    def test_polish(self):
        assert ar.exit_code_for(65, 60, 75) == 1

    def test_blocked(self):
        assert ar.exit_code_for(40, 60, 75) == 2

    def test_boundaries(self):
        assert ar.exit_code_for(75, 60, 75) == 0
        assert ar.exit_code_for(60, 60, 75) == 1
        assert ar.exit_code_for(59, 60, 75) == 2


# ─── Defaults ────────────────────────────────────────────────────────────────

class TestDefaults:
    def test_default_models(self):
        assert ar.default_model("openai") == "gpt-4o"
        assert ar.default_model("anthropic") == "claude-3-5-sonnet-latest"


import subprocess, json as _json, os

class TestAgentMode:
    def _shots(self):
        return _shots_dir(("mobile","desktop"))

    def test_agent_mode_emits_manifest(self):
        d = _shots_dir(("mobile","desktop"))
        script = str(Path(__file__).parent.parent / "scripts" / "aesthetic_review.py")
        r = subprocess.run([sys.executable, script, "--screenshots", str(d), "--archetype", "§3 Luxury"],
                           capture_output=True, text=True)
        assert r.returncode == 0
        m = _json.loads(r.stdout)
        assert m["status"] == "awaiting_agent_vision"
        assert len(m["screenshots"]) == 2
        assert "§3 Luxury" in m["rubric"]
        assert set(m["verdict_schema"]["dimensions"]) == {k for k,_ in ar.RUBRIC_DIMENSIONS}

    def test_verdict_loop_scores_and_exits(self):
        d = _shots_dir(("desktop",))
        script = str(Path(__file__).parent.parent / "scripts" / "aesthetic_review.py")
        vfile = Path(tempfile.mkdtemp()) / "verdict.json"
        vfile.write_text(_json.dumps({"overall_score": 82, "verdict": "clean", "reads_as": "human"}))
        r = subprocess.run([sys.executable, script, "--verdict", str(vfile), "--json"],
                           capture_output=True, text=True)
        assert r.returncode == 0  # 82 >= pass 75
        out = _json.loads(r.stdout)
        assert out["overall_score"] == 82 and out["exit_code"] == 0

    def test_verdict_below_floor_blocks(self):
        script = str(Path(__file__).parent.parent / "scripts" / "aesthetic_review.py")
        vfile = Path(tempfile.mkdtemp()) / "v.json"
        vfile.write_text(_json.dumps({"overall_score": 40}))
        r = subprocess.run([sys.executable, script, "--verdict", str(vfile)], capture_output=True, text=True)
        assert r.returncode == 2
