# app/dev/strands_smoke.py

import os
from app.agent.strands_safety import SafeStrandsAgent

def main():
    # Make sure STRANDS is on
    print("STRANDS_ENABLED =", os.getenv("STRANDS_ENABLED"))

    agent = SafeStrandsAgent(
        name="rih_debug_enhancer",
        instructions=(
            "You help refine responses for a university health services FAQ assistant. "
            "Improve clarity, warmth, and structure WITHOUT changing any facts, URLs, "
            "phone numbers, or appointment channels."
        ),
        allowed_topics=["counseling", "appointments", "booking"],
    )

    print("SafeStrandsAgent.enabled:", agent.enabled)

    user = "How do I book a counseling appointment and what happens in the first session?"
    base = (
        "You can schedule a counseling appointment through the patient portal or by calling "
        "the main RIH number during business hours. In a first session, you typically discuss "
        "your concerns, goals, and what kind of support might help."
    )

    print("\n=== USER TEXT ===")
    print(user)
    print("\n=== BASE RESPONSE ===")
    print(base)

    enhanced = agent.generate(user_text=user, base_response=base)

    print("\n=== ENHANCED RESPONSE ===")
    print(enhanced)

    if enhanced == base:
        print("\n[INFO] Strands returned the same text (or failed closed).")
    else:
        print("\n[INFO] Strands modified the response above.")

if __name__ == "__main__":
    main()
