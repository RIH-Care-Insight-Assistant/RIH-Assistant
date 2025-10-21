#!/usr/bin/env python3
from __future__ import annotations
import csv, sys, re
from pathlib import Path

# in scripts/propose_routing.py
LANES = {
    "urgent_safety": ["suicide","kill myself","unalive","take my life","harm myself","harm others","988","911"],
    "title_ix": ["harass","assault","rape","stalk","coercion","nonconsensual"],
    "harassment_hate": ["threat","threaten","slur","bias","bully","intimidat","doxx"],
    "retention_withdraw": ["withdraw","drop out","drop from","leave school","quit college","transfer"],
    # note: omit "appointment" on purpose; the planner’s Clarify→Retrieve flow handles it
    "counseling": ["counsel","therapy","therapist","mental health","talk to someone"],
}


def lane_for(term: str) -> str | None:
    t = term.lower()
    for lane, seeds in LANES.items():
        for s in seeds:
            if s in t:
                return lane
    return None

def main():
    src = Path("data/public_crawl/candidates.csv")
    if not src.exists():
        print("Run extract_keywords.py first", file=sys.stderr)
        sys.exit(1)

    props = []
    with src.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            term = row["term"]
            lane = lane_for(term)
            if lane:
                props.append((lane, term))

    # group terms per lane and write a proposed CSV in the same schema as routing_matrix.csv
    grouped = {}
    for lane, term in props:
        grouped.setdefault(lane, set()).add(term)

    out = Path("safety/routing_matrix_proposed.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        f.write("level,example_triggers,auto_reply_key,destination,sla,after_hours\n")
        for lane, terms in grouped.items():
            key_map = {
                "urgent_safety":"crisis",
                "title_ix":"title_ix",
                "harassment_hate":"conduct",
                "retention_withdraw":"retention",
                "counseling":"counseling",
            }
            auto = key_map[lane]
            triggers = ";".join(sorted(terms))
            # destination/sla placeholders; keep consistent with your current CSV
            dest = "Resources" if lane in {"urgent_safety"} else {
                "title_ix":"Title IX Office","harassment_hate":"Student Conduct/CARE",
                "retention_withdraw":"Advising/Student Success","counseling":"Counseling Front Desk"
            }.get(lane,"Resources")
            sla = "immediate" if lane=="urgent_safety" else "next_business_day"
            aft = "Resources"
            f.write(f"{lane},{triggers},{auto},{dest},{sla},{aft}\n")

    print("Wrote safety/routing_matrix_proposed.csv")
    print("Review & merge into safety/routing_matrix.csv after manual vetting.")

if __name__ == "__main__":
    main()
