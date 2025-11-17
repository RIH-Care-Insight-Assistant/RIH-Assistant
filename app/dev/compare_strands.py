# app/dev/compare_strands.py

import os
from app.agent.dispatcher import Dispatcher

QUESTION = "How do I book a counseling appointment?"

def run_once(label: str):
    print("=" * 80)
    print(f"RUN: {label}")
    print(f"STRANDS_ENABLED = {os.getenv('STRANDS_ENABLED')}")
    print("-" * 80)

    # Always RULE planner + Clarify v2 for the demo
    os.environ.setdefault("RIH_PLANNER", "RULE")
    os.environ.setdefault("CLARIFY_V2", "true")

    d = Dispatcher(force_mode="RULE")
    out = d.respond(QUESTION)

    text = out.get("text", "")
    trace = out.get("trace", [])

    print("TEXT:\n")
    print(text)
    print("\nTRACE EVENTS:")
    for ev in trace:
        print(ev)

    # Show whether the enhancer actually ran
    enhanced = any(ev.get("event") == "enhance" for ev in trace)
    print("\nEnhanced by Strands? ->", enhanced)
    print("=" * 80)
    print()

if __name__ == "__main__":
    run_once("Single run with current STRANDS_ENABLED")
