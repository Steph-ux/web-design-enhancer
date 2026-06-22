"""
tests/test_detect_slop_scoring.py

Gate-semantics regression for detect_ai_slop.py after the two-tier normalization.

Contract (size-independent):
  passed = (error_count == 0) AND (warning_count / files <= MAX_WARNING_DENSITY)

  - Any severity-"error" issue (contract §0b/§0d violation) BLOCKS, regardless of
    project size — fixes the small-project fail-open (1 violation used to leave
    score at 90 and PASS).
  - severity-"warning" issues (taste/quality) only block above a per-file density
    — fixes the large-project false alarm (raw -5 each used to sink big-but-clean
    projects below 80).
  - The 0-100 score is retained for human reporting only; it is NO LONGER the gate.
  - status_badge is severity "error" (was a hardcoded -8 "warning").
"""
import sys
import io
import contextlib
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from detect_ai_slop import AISloPDetector  # noqa: E402


def _run(files: dict):
    """Run the full pipeline over a synthetic project. files: {name: content}."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        for name, content in files.items():
            (tdp / name).write_text(content, encoding="utf-8")
        det = AISloPDetector(design_file=None, code_dir=str(tdp))
        with contextlib.redirect_stdout(io.StringIO()):
            passed = det.run(json_mode=False)
        return det, passed


_VP = "<head><meta name='viewport' content='width=device-width'></head>"


# --- pure gate function ----------------------------------------------------

def test_evaluate_gate_blocks_on_any_error():
    assert AISloPDetector.evaluate_gate(errors=1, warnings=0, files=50) is False


def test_evaluate_gate_passes_clean_regardless_of_size():
    assert AISloPDetector.evaluate_gate(errors=0, warnings=0, files=1) is True
    assert AISloPDetector.evaluate_gate(errors=0, warnings=0, files=99) is True


def test_evaluate_gate_warning_density_scales_with_size():
    n = AISloPDetector.MAX_WARNING_DENSITY
    # 1 file: exactly at the density ceiling passes, one over fails.
    assert AISloPDetector.evaluate_gate(0, int(n), 1) is True
    assert AISloPDetector.evaluate_gate(0, int(n) + 1, 1) is False
    # 10 files: the same warning budget per file is allowed (size independence).
    assert AISloPDetector.evaluate_gate(0, int(n) * 10, 10) is True


# --- end-to-end gate behavior ---------------------------------------------

def test_single_contract_violation_blocks_small_project():
    # One injected SYS_ACTIVE badge in a one-file project. Used to score 90 -> PASS.
    det, passed = _run({"index.html": _VP + "<span>SYS_ACTIVE</span>"})
    assert det.error_count >= 1
    assert passed is False


def test_status_badge_is_error_severity():
    det, _ = _run({"index.html": _VP + "<span>SYS_ACTIVE</span>"})
    badges = [i for i in det.issues if i["type"] == "status_badge"]
    assert badges, "status_badge issue should fire"
    assert all(b["severity"] == "error" for b in badges), "status_badge must be error-level now"


def test_clean_small_project_passes():
    det, passed = _run({"index.html": _VP + "<main><h1>Atelier Reliure</h1></main>"})
    assert det.error_count == 0
    assert passed is True


def test_large_clean_project_with_minor_noise_passes():
    # 10 css files, each with ONE warning-level issue (hardcoded hex). Old model:
    # -5 * 10 = -50 -> score 50 -> FAIL. New model: 10 warnings / 10 files = 1.0/file.
    files = {f"s{i}.css": ".x { color: #4ab3f7; }" for i in range(10)}
    det, passed = _run(files)
    assert det.error_count == 0
    assert det.warning_count >= 10
    assert det.files_count >= 10
    assert passed is True


def test_warning_dense_small_project_fails():
    # One file packed with many warning-level CSS issues -> density over ceiling.
    dense = ".a{color:#4ab3f7}.b{margin:0!important}.c{z-index:9999}" \
            ".d{font-family:monospace}.e{backdrop-filter:blur(4px)}"
    det, passed = _run({"style.css": dense})
    assert det.error_count == 0
    assert det.warning_count / max(det.files_count, 1) > AISloPDetector.MAX_WARNING_DENSITY
    assert passed is False
