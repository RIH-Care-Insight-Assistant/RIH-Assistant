"""Read-only, offline probes of C1-v0.2 behavior; not formal acceptance.

Run from the repository root: python -m scripts.audit_c1_readiness
Exit 1 means a probed requirement is unmet; exit 0 cannot establish human approval.
Only synthetic conversations and temporary synthetic KB records are used.
"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.answer.alternatives import safe_alternatives
from app.retriever import retriever
from app.tools.decline_detector import DeclineDetector


def audit() -> dict:
    checks = []

    def record(check_id, expected, probe):
        try:
            actual = probe()
            checks.append(
                {
                    "id": check_id,
                    "expected": expected,
                    "actual": actual,
                    "passed": actual == expected,
                }
            )
        except Exception as error:
            # No exception messages, filesystem paths, or retrieved text in evidence.
            checks.append({"id": check_id, "error_type": type(error).__name__, "passed": False})

    detector = DeclineDetector()
    for check_id, message, expected in [
        (
            "decline-appointment-preservation",
            "I don't want to miss my counseling appointment",
            False,
        ),
        (
            "decline-insurance-request",
            "No insurance, can I book a medical appointment?",
            False,
        ),
        ("decline-acceptance", "I'm fine with counseling", False),
        ("decline-curly-refusal", "I don\u2019t want counseling", True),
        (
            "decline-information-request",
            "I don't need an appointment, just the RIH hours",
            False,
        ),
        ("decline-explicit-refusal", "I don't want counseling", True),
        ("decline-alternative-request", "Any other options?", True),
        ("decline-bare-no", "no", False),
        ("decline-bare-nah", "nah", False),
        ("decline-bare-nope", "nope", False),
    ]:
        record(check_id, expected, lambda message=message: detector.is_decline(message))

    public = {"title": "Public", "text": "billing insurance", "allow_chat": True}
    disabled = {
        "title": "Restricted",
        "text": "billing insurance " * 20,
        "allow_chat": False,
    }
    crisis = {
        "title": "Crisis only",
        "text": "billing insurance " * 10,
        "page_type": "crisis",
    }
    with TemporaryDirectory(prefix="rih-c1-audit-") as directory:
        path = Path(directory)
        with patch.multiple(retriever, KB_DIR=path, _cached_kb=None, _idf=None, _total_docs=0):

            def seed(records):
                (path / "synthetic.jsonl").write_text(
                    "\n".join(json.dumps(item) for item in records), encoding="utf-8"
                )
                retriever._reset_cache()

            def titles(**kwargs):
                return [item["title"] for item in retriever.retrieve("billing insurance", **kwargs)]

            seed([disabled, crisis, public])
            record(
                "retrieval-filter-before-top-k",
                ["Public"],
                lambda: titles(k=3, top_k=1),
            )
            record(
                "retrieval-restricted-records-excluded",
                ["Public"],
                lambda: titles(top_k=3),
            )
            seed([disabled, crisis])
            record("retrieval-all-restricted-empty", [], titles)
            # Narrow loader robustness repair approved in Issues #6 and #7.
            seed([[], public])
            record("retrieval-non-object-robustness", ["Public"], titles)

    text = safe_alternatives()
    record("alternatives-linked-official-evidence", True, lambda: "umbc.edu/" in text)
    failed = sum(not item["passed"] for item in checks)
    return {
        "contract": "C1-v0.2 (joint approval recorded in Issue #7)",
        "scope": "synthetic offline probes; no production behavior or source files changed",
        "formal_checkpoint_acceptance": "not established by this audit",
        "checks": checks,
        "total": len(checks),
        "passed": len(checks) - failed,
        "failed": failed,
    }


def main() -> int:
    report = audit()
    print(json.dumps(report, indent=2, sort_keys=True))
    return int(report["failed"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
