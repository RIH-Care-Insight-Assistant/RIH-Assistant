"""README images: every local image exists, is a real PNG, and every committed asset is used."""

from __future__ import annotations

import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
ASSETS = ROOT / "docs" / "assets"

# Markdown images, HTML <img src>, and plain links to asset files.
REFS = set(re.findall(r'(?:!\[[^\]]*\]\(|<img src="|\]\()(docs/assets/[^)"\s]+)', README))


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path} is not a PNG"
    return struct.unpack(">II", data[16:24])


def test_readme_references_screenshots_and_diagrams():
    assert any(r.startswith("docs/assets/screenshots/") for r in REFS)
    assert "docs/assets/architecture/system-architecture.png" in REFS
    assert "docs/assets/architecture/request-flow.png" in REFS


def test_every_referenced_image_exists_and_is_a_png():
    for ref in sorted(REFS):
        path = ROOT / ref
        assert path.is_file(), f"README points to a missing file: {ref}"
        width, height = _png_size(path)
        assert width >= 390 and height >= 200, f"{ref} is unexpectedly small ({width}x{height})"


def test_every_committed_asset_is_referenced():
    on_disk = {p.relative_to(ROOT).as_posix() for p in ASSETS.rglob("*.png")}
    assert on_disk, "no assets found"
    assert on_disk <= REFS, f"unreferenced assets: {sorted(on_disk - REFS)}"


def test_diagram_sources_are_kept_next_to_the_docs():
    for name in ("architecture.html", "request-flow.html", "diagram.css"):
        assert (ROOT / "docs" / "architecture" / "diagrams" / name).is_file()
