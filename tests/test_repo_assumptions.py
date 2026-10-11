# tests/test_repo_assumptions.py
"""
C1 / Phase 0: executable checks for repository and CI assumptions that the two
contributors' environments (WSL2/Ubuntu, macOS, GitHub Actions) rely on.
Pure file inspection; no git, network, or optional dependencies required.
"""
from __future__ import annotations

import csv
import importlib
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".py", ".md", ".csv", ".json", ".jsonl", ".txt", ".toml", ".yml", ".yaml", ".cfg", ".ini"}
SKIP_DIRS = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache", "build", "dist"}


def _repo_text_files():
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in TEXT_SUFFIXES and not (set(p.relative_to(ROOT).parts) & SKIP_DIRS):
            yield p


def test_text_files_use_lf_line_endings():
    crlf = [str(p.relative_to(ROOT)) for p in _repo_text_files() if b"\r\n" in p.read_bytes()]
    assert crlf == [], f"CRLF line endings (see .gitattributes): {crlf}"


def test_no_invisible_or_bidi_control_characters():
    # "Trojan Source" guard: invisible format characters (zero-width, bidi controls, BOM)
    # cannot be reviewed by eye. Test data that needs them must use \\uXXXX escapes.
    import unicodedata

    hits = []
    for p in _repo_text_files():
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            bad = sorted({f"U+{ord(c):04X}" for c in line if unicodedata.category(c) == "Cf"})
            if bad:
                hits.append(f"{p.relative_to(ROOT)}:{n} {','.join(bad)}")
    assert hits == []


def test_gitattributes_enforces_lf():
    text = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert re.search(r"^\*\s+text=auto\s+eol=lf\b", text, re.M)


# Machine-specific absolute paths that would break on the other contributor's OS or CI.
_ABS_PATH_RE = re.compile(r"([A-Za-z]:\\\\?Users\\|/Users/[A-Za-z]|/home/[A-Za-z]|/mnt/[a-z]/)")


def test_no_machine_specific_absolute_paths_in_code():
    hits = []
    for sub in ("app", "scripts", "tests"):
        for p in (ROOT / sub).rglob("*.py"):
            if p.name == pathlib.Path(__file__).name:
                continue
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if _ABS_PATH_RE.search(line):
                    hits.append(f"{p.relative_to(ROOT)}:{n}")
    assert hits == []


def test_ci_workflow_runs_tests_and_safety_gate():
    wf = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "pytest" in wf
    assert "scripts/safety_eval.py" in wf and "--fail-on-miss" in wf
    assert "ruff check" in wf
    # Least-privilege token and SHA-pinned third-party actions.
    assert re.search(r"^permissions:\s*\n\s+contents:\s*read", wf, re.M)
    for ref in re.findall(r"uses:\s*(\S+)", wf):
        assert re.search(r"@[0-9a-f]{40}$", ref), f"action not pinned to a commit SHA: {ref}"


_STATE_DOCS = (
    "AGENTS.md", "CLAUDE.md", "docs/MASTER_PLAN.md", "docs/PROJECT_STATE.md", "docs/RELEASE_GATES.md",
)
_LOCAL_LINK_RE = re.compile(r"\]\((?!https?://|#)([^)#\s]+)")


@pytest.mark.parametrize("doc", _STATE_DOCS)
def test_agent_state_docs_link_to_existing_files(doc):
    # A new Codex or Claude session starts from these files; a dead link loses context.
    path = ROOT / doc
    links = _LOCAL_LINK_RE.findall(path.read_text(encoding="utf-8"))
    assert links, f"{doc} has no relative links; did the link format change?"
    missing = [link for link in links if not (path.parent / link).exists()]
    assert missing == [], f"{doc} links to missing files: {missing}"


def test_claude_md_imports_agents_md():
    # One set of standards for every agent: CLAUDE.md must not fork AGENTS.md.
    assert re.search(r"^@AGENTS\.md\s*$", (ROOT / "CLAUDE.md").read_text(encoding="utf-8"), re.M)


def test_routing_matrix_schema():
    with (ROOT / "safety" / "routing_matrix.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows
    for row in rows:
        assert (row.get("category") or row.get("level")), row
        assert (row.get("response_key") or row.get("auto_reply_key")), row
    assert "urgent_safety" in {(r.get("category") or r.get("level")) for r in rows}


_OPTIONAL_DEV_MODULES = ("app.dev.",)  # manual demo scripts, not part of the runtime

# app/ subfolders are namespace packages (no __init__.py), so pkgutil cannot walk them;
# enumerate the source files instead.
APP_MODULES = sorted(
    ".".join(p.relative_to(ROOT).with_suffix("").parts)
    for p in (ROOT / "app").rglob("*.py")
    if p.name != "__init__.py" and "__pycache__" not in p.parts
)
RUNTIME_MODULES = [m for m in APP_MODULES if not m.startswith(_OPTIONAL_DEV_MODULES)]


def test_module_discovery_found_the_runtime():
    # Guards against this check silently testing nothing.
    assert {"app.router.rules", "app.agent.dispatcher", "app.ui.cli"} <= set(RUNTIME_MODULES)


@pytest.mark.parametrize("name", RUNTIME_MODULES)
def test_every_app_module_imports(name):
    importlib.import_module(name)
