"""Assemble the static portfolio showcase into var/showcase/ (gitignored).

Only images listed in showcase/manifest.json (approved by both humans) are copied, and each must
still match its pinned SHA-256. The page must stay non-interactive: no scripts, forms, inputs,
frames, external URLs or API paths. The build fails closed on any mismatch. It never deploys.

    python scripts/build_showcase.py [--out var/showcase]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "showcase"

FORBIDDEN = [
    (re.compile(r"<\s*(script|form|input|textarea|select|button|iframe|object|embed)\b", re.I), "interactive element"),
    (re.compile(r"\bon[a-z]+\s*=", re.I), "inline event handler"),
    (re.compile(r"(?:src|href)\s*=\s*\"(?:https?:)?//", re.I), "external URL"),
    (re.compile(r"/api/", re.I), "API path"),
]


def check(manifest: dict, html: str) -> list[str]:
    """Return a list of problems; empty means the showcase may be assembled."""
    problems: list[str] = []
    disclaimer = manifest["required_disclaimer"]
    if disclaimer not in html:
        problems.append("page is missing the required disclaimer")
    if "Content-Security-Policy" not in html:
        problems.append("page has no Content-Security-Policy")
    for pattern, label in FORBIDDEN:
        if pattern.search(html):
            problems.append(f"page contains a forbidden {label}")

    approved = {Path(item["source"]).name: item for item in manifest["approved"]}
    used = set(re.findall(r'<img\s+src="assets/([^"]+)"', html))
    for name in sorted(used - approved.keys()):
        problems.append(f"page uses an image that is not approved: {name}")
    for name in sorted(approved.keys() - used):
        problems.append(f"approved image is not on the page: {name}")

    for item in manifest["approved"]:
        path = ROOT / item["source"]
        if not path.is_file():
            problems.append(f"{item['id']}: missing file {item['source']}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item["sha256"]:
            problems.append(f"{item['id']}: {item['source']} changed since approval; it needs a new review")
        caption = item.get("required_caption")
        if caption and caption not in html:
            problems.append(f"{item['id']}: required caption is missing")
    return problems


def build(out: Path) -> Path:
    manifest = json.loads((SRC / "manifest.json").read_text(encoding="utf-8"))
    html = (SRC / "index.html").read_text(encoding="utf-8")
    problems = check(manifest, html)
    if problems:
        raise SystemExit("showcase build refused:\n  " + "\n  ".join(problems))
    if out.exists():
        shutil.rmtree(out)
    (out / "assets").mkdir(parents=True)
    shutil.copyfile(SRC / "index.html", out / "index.html")
    shutil.copyfile(SRC / "showcase.css", out / "showcase.css")
    for item in manifest["approved"]:
        shutil.copyfile(ROOT / item["source"], out / "assets" / Path(item["source"]).name)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(ROOT / "var" / "showcase"))
    args = parser.parse_args(argv)
    out = build(Path(args.out))
    files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
    print(f"showcase assembled in {out} ({len(files)} files); not deployed")
    for name in files:
        print(f"  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
