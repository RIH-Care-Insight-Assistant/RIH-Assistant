# app/answer/compose.py
from __future__ import annotations
from typing import List, Dict

# --- Templates (unchanged content) ---
TEMPLATES = {
    "crisis": (
        "If you might be in danger or considering self-harm: Call 911 or 988 now. "
        "On campus, contact UMBC Police (410-455-5555). RIH Urgent Care: 410-455-2542. "
        "I can’t proceed with a normal answer, but you’re not alone."
    ),
    "title_ix": (
        "Title IX support: Report or seek confidential guidance. Title IX Office: 410-455-1717. "
        "You can learn about options and supportive measures without making a formal report."
    ),
    "conduct": (
        "Student Conduct/CARE resources can help with harassment, bias, or threats. "
        "We can connect you with support, safety planning, and reporting options."
    ),
    "retention": (
        "Thinking about withdrawing or taking a break? Academic Advising and Student Success can help "
        "you explore options, deadlines, and impacts before you decide."
    ),
    "counseling": (
        "Counseling at RIH: appointments, brief therapy, referrals, and workshops are available. "
        "If this is urgent, see crisis options above."
    ),
}

# --- One-time disclaimer for session start (CLI prints once) ---
DISCLAIMER_TEXT = (
    "I'm an informational assistant for Retriever Integrated Health (RIH). "
    "I don’t provide medical advice. In emergencies, call 911 or 988. "
    "On campus, contact UMBC Police (410-455-5555)."
)

def render_template(key: str) -> str:
    return TEMPLATES.get(key, "I’ll point you to the right campus resource.")

def compose_answer(query: str, chunks: List[Dict]) -> str:
    if not chunks:
        return (
            "I couldn’t find a specific page in the knowledge base yet. "
            "Try rephrasing or ask about hours, appointments, billing, or counseling."
        )

    # numbered bullets + Sources section (titles + URLs)
    lines = ["Here’s what I found:"]
    sources: List[str] = []
    for i, c in enumerate(chunks[:3], start=1):
        title = c.get("title", "RIH")
        url = c.get("url", "")
        text = (c.get("text", "") or "").strip()
        snippet = text[:220].rstrip()
        lines.append(f"[{i}] {title}: {snippet}")
        if url:
            sources.append(f"[{i}] {title} ({url})")
        else:
            sources.append(f"[{i}] {title}")

    if sources:
        lines.append("\nSources:")
        lines.extend(sources)

    return "\n".join(lines)

# --- Legacy shims (keep old CLI imports working) ---
def disclaimer() -> str:
    return DISCLAIMER_TEXT

def from_chunks(chunks: List[Dict], *, query: str | None = None) -> str:
    return compose_answer(query=query or "", chunks=chunks)

def crisis_message() -> str:
    return render_template("crisis")

def template_for(key: str) -> str:
    return render_template(key)
