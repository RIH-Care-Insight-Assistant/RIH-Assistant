"""Curated public informational alternatives; no runtime network or model calls."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from urllib.parse import urlsplit


@dataclass(frozen=True)
class _Resource:
    title: str
    url: str
    description: str
    verified_on: date | None
    enabled: bool = True  # Maintainers can withdraw a resource without replacing it.


# Official pages inspected on this date; this is not a live availability check
# or a new freshness policy. Source evidence is recorded in the C1 repair report.
_RESOURCES = (
    _Resource(
        "Retriever Essentials",
        "https://retrieveressentials.umbc.edu/",
        "Food-access information.",
        date(2026, 10, 11),
    ),
    _Resource(
        "Academic Success Center",
        "https://academicsuccess.umbc.edu/",
        "Academic support and tutoring information.",
        date(2026, 10, 11),
    ),
    _Resource(
        "The Gathering Space for Spiritual Well-Being",
        "https://campuslife.umbc.edu/belonging/the-gathering-space/",
        "Community and spiritual reflection information.",
        date(2026, 10, 11),
    ),
)


def safe_alternatives() -> str:
    """Return inspected official links or clarification if none remain verified.

    Verification records are maintained in code, not inferred from retrieved
    content. The dispatcher keeps safety/retention guidance ahead of this helper.
    """
    lines = []
    for resource in _RESOURCES:
        try:
            url = urlsplit(resource.url)
            host = url.hostname or ""
        except (TypeError, ValueError):
            continue
        if (
            resource.enabled
            and isinstance(resource.verified_on, date)
            and url.scheme == "https"
            and (host == "umbc.edu" or host.endswith(".umbc.edu"))
            and url.username is None
            and url.password is None
        ):
            lines.append(f"- **[{resource.title}]({resource.url})**: {resource.description}")
    if lines:
        body = "Thanks for sharing that. Here are some other UMBC resources with official information:\n\n"
        body += "\n".join(lines)
        body += "\n\nCheck the official pages for current details."
    else:
        body = "I don't have a verified alternative to recommend right now."
    return (
        body + " These informational resources are not substitutes for medical, counseling, "
        "or emergency support. What kind of support are you looking for?"
    )
