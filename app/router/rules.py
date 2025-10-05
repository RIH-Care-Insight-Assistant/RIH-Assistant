
# Purpose: Load routing rules from safety/routing_matrix.csv (if present),
# Otherwise fall back to safe built‑in defaults matching your
# previous hardcoded patterns (including routing all 'harass*' → Title IX).

# app/router/rules.py
from __future__ import annotations
# CSV-driven rules loader (supports legacy schema + new schema)
# - Legacy columns supported: level,example_triggers,auto_reply_key,destination,sla,after_hours
# - New columns supported:   category,response_key,priority,example_triggers
# - Triggers split on ; | ,   (any of them)
# - Merges CSV with safe defaults for any missing categories
# - Env:
#   RIH_ROUTING_REQUIRE_CSV=1            -> error if CSV missing
#   RIH_ROUTE_APPOINTMENT_TO_COUNSELING=1-> keep "appointment(s)" triggers in counseling (default: filter out)

import csv
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Pattern, Tuple

CSV_PATH = Path(__file__).resolve().parents[2] / "safety" / "routing_matrix.csv"
REQUIRE_CSV = os.getenv("RIH_ROUTING_REQUIRE_CSV") == "1"
ROUTE_APPT_TO_COUNSELING = os.getenv("RIH_ROUTE_APPOINTMENT_TO_COUNSELING") == "1"

BOUNDARY_WORD = r"(?<![A-Za-z0-9_]){p}(?![A-Za-z0-9_])"

NORMALIZE_MAP = {
    # Title IX / harassment variants
    "harrased": "harassed",
    "harrasment": "harassment",
    "harrassment": "harassment",
    # Safety variants
    "unalive": "kill myself",
    "kms": "kill myself",
    "kys": "kill myself",
    "sucide": "suicide",
    "commited suicide": "committed suicide",
    # Retention phrasing
    "drop from college": "drop out",
    "leave uni": "leave university",
}

# default priority order if 'priority' not provided
DEFAULT_PRIORITY = {
    "urgent_safety": 1,
    "title_ix": 2,
    "harassment_hate": 3,
    "retention_withdraw": 4,
    "counseling": 5,
}

@dataclass
class Rule:
    category: str                 # urgent_safety | title_ix | harassment_hate | retention_withdraw | counseling
    response_key: str             # maps to compose template key ("crisis", "title_ix", etc.)
    patterns: List[Pattern]
    priority: int                 # lower = higher priority

class Rules:
    def __init__(self, csv_path: Path = CSV_PATH):
        self.csv_path = csv_path
        self.by_category: Dict[str, Rule] = {}
        self._load()

    @staticmethod
    def _compile_terms(terms: List[str]) -> List[Pattern]:
        pats: List[Pattern] = []
        for t in terms:
            t = t.strip()
            if not t:
                continue
            esc = re.escape(t).replace(r"\ ", r"\s+")  # flexible whitespace in phrases
            pats.append(re.compile(BOUNDARY_WORD.format(p=esc), flags=re.IGNORECASE))
        return pats

    @staticmethod
    def normalize(text: str) -> str:
        t = (text or "").lower()
        for wrong, right in NORMALIZE_MAP.items():
            t = t.replace(wrong, right)
        return t

    def _defaults_dict(self) -> Dict[str, Rule]:
        # Safe defaults mirror our current policy (generic harass → Title IX)
        SLANG_URGENCY = [r"\bkms\b", r"\bunalive\b"]
        PHRASES_URGENCY = [
            r"\bkill myself\b", r"\bsuicide\b", r"\bend it\b",
            r"\bhurt (myself|others)\b", r"\btake my life\b", r"\bno reason to live\b",
        ]
        TITLE_IX = [
            r"\bsex(ual)?\s*(assault|harass(ed|ment|ing)?|misconduct|coercion)\b",
            r"\bharass(ed|ment|ing)?\b",
            r"\b(non\s*-?\s*consensual|nonconsensual)\b",
            r"\brape\b", r"\bstalk(ing)?\b",
        ]
        CONDUCT = [
            r"\bslur\b", r"\bhate\b", r"\bracist\b", r"\bhomophobic\b", r"\bableist\b",
            r"\bthreat(s|en|ening)?\b", r"\bbully(ing)?\b", r"\bintimidat(e|ion|ing)?\b",
            r"\bdoxx(ing)?\b", r"\btargeted harassment\b",
        ]
        RETENTION = [r"\b(withdraw|transfer|drop\s?out|leave school|quit college)\b"]
        COUNSELING = [r"\b(counsel(ing)?|therapy|therapist|mental health|talk to (someone|a counselor))\b"]

        return {
            "urgent_safety": Rule("urgent_safety", "crisis", [re.compile("|".join(SLANG_URGENCY + PHRASES_URGENCY), re.I)], DEFAULT_PRIORITY["urgent_safety"]),
            "title_ix": Rule("title_ix", "title_ix", [re.compile("|".join(TITLE_IX), re.I)], DEFAULT_PRIORITY["title_ix"]),
            "harassment_hate": Rule("harassment_hate", "conduct", [re.compile("|".join(CONDUCT), re.I)], DEFAULT_PRIORITY["harassment_hate"]),
            "retention_withdraw": Rule("retention_withdraw", "retention", [re.compile("|".join(RETENTION), re.I)], DEFAULT_PRIORITY["retention_withdraw"]),
            "counseling": Rule("counseling", "counseling", [re.compile("|".join(COUNSELING), re.I)], DEFAULT_PRIORITY["counseling"]),
        }

    def _split_triggers(self, s: str) -> List[str]:
        # split on ; or | or , and strip
        return [t.strip() for t in re.split(r"[;|,]", s or "") if t.strip()]

    def _load_from_csv(self) -> Dict[str, Rule]:
        rules: Dict[str, Rule] = {}
        if not self.csv_path.exists():
            return rules
        with self.csv_path.open(newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # normalize headers
                norm = { (k or "").strip().lower(): (v or "").strip() for k, v in row.items() }

                # support both schemas
                category = norm.get("category") or norm.get("level") or ""
                if not category:
                    continue

                response_key = norm.get("response_key") or norm.get("auto_reply_key") or category

                # priority (use provided if present, else default order)
                try:
                    priority = int(norm.get("priority") or DEFAULT_PRIORITY.get(category, 100))
                except ValueError:
                    priority = DEFAULT_PRIORITY.get(category, 100)

                # triggers (semicolon or pipe or comma)
                triggers_raw = norm.get("example_triggers", "")
                terms = self._split_triggers(triggers_raw)

                # optional filtering: remove "appointment(s)" from counseling unless explicitly allowed
                if category == "counseling" and not ROUTE_APPT_TO_COUNSELING:
                    filtered = [t for t in terms if t.lower() not in {"appointment", "appointments"}]
                    if len(filtered) != len(terms):
                        print("[RIH Router] INFO: filtered 'appointment(s)' from counseling triggers (default behavior). "
                              "Set RIH_ROUTE_APPOINTMENT_TO_COUNSELING=1 to keep.", file=sys.stderr)
                    terms = filtered

                pats = self._compile_terms(terms) if terms else []
                if pats:
                    rules[category] = Rule(category, response_key, pats, priority)
        return rules

    def _load(self) -> None:
        defaults = self._defaults_dict()
        csv_rules = self._load_from_csv()

        if REQUIRE_CSV and not csv_rules:
            print("[RIH Router] ERROR: routing_matrix.csv not found but RIH_ROUTING_REQUIRE_CSV=1", file=sys.stderr)
            raise FileNotFoundError(f"Missing required CSV: {self.csv_path}")

        if not csv_rules:
            print(f"[RIH Router] WARNING: using built-in defaults (no CSV at {self.csv_path})", file=sys.stderr)

        merged = defaults.copy()
        merged.update(csv_rules)  # CSV overrides present categories
        self.by_category = merged

    def match(self, text: str) -> Tuple[str | None, str | None]:
        t = self.normalize(text)
        for rule in sorted(self.by_category.values(), key=lambda r: r.priority):
            for pat in rule.patterns:
                if pat.search(t):
                    return rule.category, rule.response_key
        return None, None

            r"\bharass(ed|ment|ing)?\b",
            r"\b(non\s*-?\s*consensual|nonconsensual)\b",
            r"\brape\b", r"\bstalk(ing)?\b",
        ]
        CONDUCT = [
            r"\bslur\b", r"\bhate\b", r"\bracist\b", r"\bhomophobic\b", r"\bableist\b",
            r"\bthreat(s|en|ening)?\b", r"\bbully(ing)?\b", r"\bintimidat(e|ion|ing)?\b",
            r"\bdoxx(ing)?\b", r"\btargeted harassment\b",
        ]
        RETENTION = [r"\b(withdraw|transfer|drop\s?out|leave school|quit college)\b"]
        COUNSELING = [r"\b(counsel(ing)?|therapy|therapist|mental health|talk to (someone|a counselor))\b"]

        return {
            "urgent_safety": Rule("urgent_safety", "crisis", [re.compile("|".join(SLANG_URGENCY + PHRASES_URGENCY), re.I)], 1),
            "title_ix": Rule("title_ix", "title_ix", [re.compile("|".join(TITLE_IX), re.I)], 2),
            "harassment_hate": Rule("harassment_hate", "conduct", [re.compile("|".join(CONDUCT), re.I)], 3),
            "retention_withdraw": Rule("retention_withdraw", "retention", [re.compile("|".join(RETENTION), re.I)], 4),
            "counseling": Rule("counseling", "counseling", [re.compile("|".join(COUNSELING), re.I)], 5),
        }

    def _load_from_csv(self) -> Dict[str, Rule]:
        rules: Dict[str, Rule] = {}
        if not self.csv_path.exists():
            return rules
        with self.csv_path.open(newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                category = (row.get("category") or "").strip()
                if not category:
                    continue
                response_key = (row.get("response_key") or category).strip()
                try:
                    priority = int((row.get("priority") or 100))
                except ValueError:
                    priority = 100
                raw_triggers = (row.get("example_triggers") or "").strip()
                terms = [s.strip() for s in re.split(r"[|,]", raw_triggers) if s.strip()]
                pats = self._compile_terms(terms) if terms else []
                if pats:
                    rules[category] = Rule(category, response_key, pats, priority)
        return rules

    def _load(self) -> None:
        # NEW: merge CSV rules (if any) with defaults for any missing categories
        defaults = self._defaults_dict()
        csv_rules = self._load_from_csv()  # may be partial
        merged = defaults.copy()
        merged.update(csv_rules)  # CSV overrides specific categories; others keep defaults
        self.by_category = merged

    def match(self, text: str) -> Tuple[str | None, str | None]:
        """Return (category, response_key) if matched else (None, None)."""
        t = self.normalize(text)
        for rule in sorted(self.by_category.values(), key=lambda r: r.priority):
            for pat in rule.patterns:
                if pat.search(t):
                    return rule.category, rule.response_key
        return None, None
