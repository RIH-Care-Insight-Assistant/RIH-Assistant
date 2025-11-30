# app/answer/alternatives.py

from __future__ import annotations


def safe_alternatives() -> str:
    """
    Phase 7: Safe, non-medical alternatives when a student declines RIH services.

    This does NOT replace medical care; it just highlights other campus supports.
    """
    return (
        "Thanks for letting me know. If you’re not interested in counseling or medical care right now, "
        "here are some other UMBC resources you might find helpful:\n\n"
        "- **The Gathering Space for Spiritual Well-Being (i3b):** Community, reflection, and support "
        "around meaning, identity, and belonging.\n"
        "- **Retriever Essentials:** Free food and essential supplies for students experiencing food insecurity.\n"
        "- **UMBC RAC (Recreation Center):** Gym, fitness classes, and recreation spaces that can support "
        "stress relief and physical well-being.\n"
        "- **Library & Study Spaces:** Quiet study areas, research help, and places to focus or recharge.\n"
        "- **Academic Success Center:** Tutoring, coaching, and academic skills support.\n"
        "- **Campus Life & Student Organizations:** Student orgs, events, and community-building activities.\n"
        "- **Career Center:** Support with internships, jobs, and career planning.\n\n"
        "If you ever decide you’d like to connect with Retriever Integrated Health again later, "
        "you can always schedule through the patient portal or by calling their main number."
    )
