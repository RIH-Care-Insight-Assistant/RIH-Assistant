"""Release-candidate identity: a digest of the committed release-relevant content (L-D13).

The candidate is defined by `governance/release_candidate.json`: the git blobs of the included
top-level paths at HEAD. Documentation and evidence are excluded, so committing the evidence of a
run does not change the candidate it describes; any change to code, configuration, tests,
datasets or governance files does. The digest uses git's normalized blob hashes, so it is the same
on Windows, WSL2 and CI. Uncommitted or untracked changes in an included path make the candidate
unidentifiable (`clean` is False), and every tracked top-level path must be classified in the
manifest; anything else is a problem that keeps readiness `not_ready`.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from .register import ROOT

MANIFEST_PATH = ROOT / "governance" / "release_candidate.json"


def load_manifest(path: Path = MANIFEST_PATH) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_problems(manifest: Dict[str, Any], tracked_top_level: set[str]) -> List[str]:
    include = list(manifest.get("include", []))
    exclude = [e.get("path") for e in manifest.get("exclude", [])]
    problems: List[str] = []
    if not manifest.get("manifest_version"):
        problems.append("candidate manifest has no version")
    if not include:
        problems.append("candidate manifest includes nothing")
    for e in manifest.get("exclude", []):
        if not str(e.get("reason", "")).strip():
            problems.append(f"candidate manifest: excluded path {e.get('path')} has no reason")
    both = set(include) & set(exclude)
    if both:
        problems.append(f"candidate manifest lists paths as both included and excluded: {sorted(both)}")
    if len(include) + len(exclude) != len(set(include) | set(exclude)):
        problems.append("candidate manifest lists a path twice")
    unlisted = sorted(tracked_top_level - set(include) - set(exclude))
    if unlisted:
        problems.append(f"tracked paths not classified in the candidate manifest: {unlisted}")
    return problems


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True,
                          encoding="utf-8", errors="replace").stdout


def compute(root: Path = ROOT, manifest: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Identity of the current tree. `digest` is None when it cannot be determined."""
    try:
        manifest = manifest if manifest is not None else load_manifest(root / "governance" / "release_candidate.json")
    except (OSError, ValueError):
        return {"manifest_version": None, "digest": None, "git_commit": None, "clean": False,
                "problems": ["candidate manifest cannot be loaded"]}
    out: Dict[str, Any] = {"manifest_version": manifest.get("manifest_version"), "digest": None,
                           "git_commit": None, "clean": False, "problems": []}
    try:
        tracked = [p for p in _git(root, "ls-files", "-z").split("\0") if p]
        out["problems"] = manifest_problems(manifest, {p.split("/", 1)[0] for p in tracked})
        include = list(manifest.get("include", []))
        out["git_commit"] = _git(root, "rev-parse", "--short", "HEAD").strip()
        tree = sorted(e for e in _git(root, "ls-tree", "-r", "-z", "HEAD", "--", *include).split("\0") if e)
        status = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", *include)
    except (OSError, subprocess.CalledProcessError):
        out["problems"] = ["git is unavailable, so the candidate cannot be identified"]
        return out
    h = hashlib.sha256(f"{out['manifest_version']}\n".encode("utf-8"))
    for entry in tree:
        h.update(entry.encode("utf-8") + b"\n")
    out["digest"] = h.hexdigest()
    out["clean"] = status == ""
    out["file_count"] = len(tree)
    return out
