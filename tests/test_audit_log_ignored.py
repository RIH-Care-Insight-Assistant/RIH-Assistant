# tests/test_audit_log_ignored.py
"""
C1 close-out (audit O6): runtime audit logs must never be committed.
app/ui/audit.py writes its log relative to the current working directory, so
the path must be ignored wherever the CLI is started inside the checkout.
Uses `git check-ignore`, so it skips outside a git checkout.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess

import pytest

from app.ui import audit

ROOT = pathlib.Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None or not (ROOT / ".git").exists(),
    reason="needs git and a git checkout",
)


@pytest.mark.parametrize("cwd", [".", "tests", "scripts"])
def test_audit_log_path_is_git_ignored(cwd):
    rel = (pathlib.PurePosixPath(cwd) / audit.LOG.as_posix()).as_posix()
    # --no-index: judge the path by .gitignore rules even if it were tracked.
    result = subprocess.run(["git", "check-ignore", "-q", "--no-index", rel], cwd=ROOT)
    assert result.returncode == 0, f"{rel} is not ignored; runtime logs could be committed"


def test_no_runtime_logs_are_tracked():
    tracked = subprocess.run(
        ["git", "ls-files", "--", ":(glob)**/app/logs/**"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    assert tracked == []
