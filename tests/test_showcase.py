"""Static showcase: only jointly approved images, pinned by hash, on a page nobody can interact with."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "showcase" / "manifest.json").read_text(encoding="utf-8"))
HTML = (ROOT / "showcase" / "index.html").read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("build_showcase", ROOT / "scripts" / "build_showcase.py")
build_showcase = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_showcase)


def test_page_and_manifest_pass_the_build_checks():
    assert build_showcase.check(MANIFEST, HTML) == []


def test_excluded_images_are_not_approved_or_used():
    approved = {item["id"] for item in MANIFEST["approved"]}
    assert {"S3", "S7", "S8", "S12"} == set(MANIFEST["excluded"])
    assert not approved & set(MANIFEST["excluded"])
    for name in ("chat-safety-guidance.png", "mobile-chat.png", "mobile-resources.png", "governance-risk-register.png"):
        assert name not in HTML


def test_check_refuses_unapproved_or_changed_images_and_interactive_markup():
    extra = HTML.replace("</main>", '<img src="assets/mobile-chat.png" alt=""></main>')
    assert any("not approved" in p for p in build_showcase.check(MANIFEST, extra))

    tampered = json.loads(json.dumps(MANIFEST))
    tampered["approved"][0]["sha256"] = "0" * 64
    assert any("changed since approval" in p for p in build_showcase.check(tampered, HTML))

    for snippet in ("<script>x()</script>", '<form action="/api/v1/chat"></form>', '<img src="https://example.org/a.png" alt="">'):
        assert build_showcase.check(MANIFEST, HTML.replace("</main>", snippet + "</main>"))


def test_build_copies_only_approved_files(tmp_path):
    out = build_showcase.build(tmp_path / "site")
    files = {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}
    expected = {"index.html", "showcase.css"} | {f"assets/{Path(i['source']).name}" for i in MANIFEST["approved"]}
    assert files == expected
