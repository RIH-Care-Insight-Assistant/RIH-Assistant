DISCLAIMER = "I'm a campus assistant and not monitored 24/7. For emergencies call 911 or 988.\n"

CRISIS_TEXT = (
    "If you’re in immediate danger or thinking about harming yourself or others, call 911 or 988 (Suicide & Crisis Lifeline). "
    "Campus Police: (410) 455-5555 or 911 (24/7). RIH Urgent Line: 410-455-2542. Title IX: 410-455-1717. "
    "I'm a campus assistant and not monitored 24/7."
)

TEMPLATES = {
    "crisis": CRISIS_TEXT,
    "title_ix": "I’m a campus assistant. For confidential support and reporting options, contact the Title IX Office at 410-455-1717 or: https://ecr.umbc.edu/gender-discrimination-sexual-misconduct/. If this is an emergency, call 911/988.",
    "conduct": "I’m a campus assistant. You can report behavior or get support via Student Conduct/CARE (https://conduct.umbc.edu/). If you feel unsafe, call 911 or Campus Police (410) 455-5555.",
    "retention": "If you’re considering withdrawing or transferring, you can review options with Advising/Student Success (contact: (410)-455-2729).",
    "counseling": "You can schedule counseling or get information via RIH Counseling (https://health.umbc.edu/counseling-services/counseling/).",
}

def disclaimer() -> str:
    return DISCLAIMER

def crisis_message() -> str:
    return TEMPLATES["crisis"]

def template_for(key: str) -> str:
    return TEMPLATES.get(key, "")

def from_chunks(chunks: list[dict]) -> str:
    if not chunks:
        return DISCLAIMER + "I couldn't find that in the RIH info I have. Try rephrasing or visit the RIH site."
    lines = [DISCLAIMER, "Here's what I found:"]
    for c in chunks:
        title = c.get("title") or "Source"
        snippet = (c.get("summary") or c.get("text") or "").strip()
        snippet = (snippet[:220] + "…") if len(snippet) > 220 else snippet
        url = c.get("url") or ""
        lines.append(f"- {title}: {snippet} ({url})")
    return "\n".join(lines)
