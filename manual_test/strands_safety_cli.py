#!/usr/bin/env python3
import os, sys
os.environ.setdefault("STRANDS_ENABLED", os.getenv("STRANDS_ENABLED","false"))
os.environ.setdefault("STRANDS_TIMEOUT_SECONDS", os.getenv("STRANDS_TIMEOUT_SECONDS","10.0"))

from app.agent.strands_safety import SafeStrandsAgent

def main():
    print("== Strands Safety Wrapper (type 'exit' to quit) ==")
    agent = SafeStrandsAgent(
        name="demo_strands",
        instructions="Echo back the message plainly.",
        allowed_topics=["tone improvement","appointments","scheduling"]
    )
    while True:
        try:
            msg = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye")
            break
        if msg.lower() in {"exit","quit"}:
            print("Bye"); break
        out = agent.safe_run(msg)
        print("Agent>", out if out else "[blocked/empty (safety/timeout/disabled)]")

if __name__ == "__main__":
    main()
