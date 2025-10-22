def plan(self, route_level: str | None, user_text: str) -> List[PlanStep]:
    t = (user_text or "").lower()

    # 1) Safety already handled by dispatcher, but keep a hard guard:
    if route_level == "urgent_safety":
        return [{"tool": "crisis", "input": {}}]

    # 2) Category tools with special handling for counseling
    if route_level in {"title_ix", "harassment_hate", "retention_withdraw", "counseling"}:
        if route_level == "counseling":
            # --- Appointment-like markers → Clarify → Retrieve
            _APPT_WORDS = {"appointment", "appointments", "schedule", "scheduling", "book", "booking"}
            _APPT_AMBIG_WORDS = {"session", "sessions", "visit", "intake", "reschedule", "cancel", "availability", "walk-in", "same-day"}
            apptish = any(w in t for w in _APPT_WORDS | _APPT_AMBIG_WORDS)
            if apptish and not _has_medical_marker(t):
                return [
                    {"tool": "clarify", "input": {
                        "kind": "counseling_vs_medical_appt",
                        "question": "Do you want to schedule a **counseling** appointment or a **medical** appointment?",
                        "options": ["counseling", "medical"]
                    }},
                    {"tool": "retrieve", "input": {"query": user_text}},
                ]

            # --- Group/workshop/scheduling intents (without explicit 'appointment') → Retrieve
            _GROUP_MARKERS = {"workshop", "support group", "group counseling", "groups"}
            _SCHED_MARKERS = {"schedule", "scheduling", "reschedule", "cancel", "session", "sessions"}
            if any(m in t for m in _GROUP_MARKERS | _SCHED_MARKERS):
                return [{"tool": "retrieve", "input": {"query": user_text}}]

            # --- Otherwise, plain counseling informational → template
            return [{"tool": "counseling", "input": {}}]

        # Non-counseling lanes default to their templates
        tool = "retention" if route_level == "retention_withdraw" else route_level
        return [{"tool": tool, "input": {}}]

    # 3) Default routing with deterministic clarify for appointment-like queries
    if _contains_any(t, ["appointment", "appointments"]) and not _has_medical_marker(t):
        return [
            {"tool": "clarify", "input": {
                "kind": "counseling_vs_medical_appt",
                "question": "Do you want to schedule a **counseling** appointment or a **medical** appointment?",
                "options": ["counseling", "medical"]
            }},
            {"tool": "retrieve", "input": {"query": user_text}},
        ]

    # 4) Default helpful behavior
    return [{"tool": "retrieve", "input": {"query": user_text}}]
