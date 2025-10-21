
# Purpose: Load routing rules from safety/routing_matrix.csv (if present),
# Otherwise fall back to safe built‑in defaults matching your
# previous hardcoded patterns (including routing all 'harass*' → Title IX).

# app/router/rules.py
from __future__ import annotations
# data-driven rules loader with safe defaults + MERGE behavior

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Pattern, Tuple

CSV_PATH = Path(__file__).resolve().parents[2] / "safety" / "routing_matrix.csv"

BOUNDARY_WORD = r"(?<![A-Za-z0-9_]){p}(?![A-Za-z0-9_])"

NORMALIZE_MAP = {
    # Title IX / harassment variants
    "harrased": "harassed",
    "harrassed": "harassed",
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
            esc = re.escape(t).replace(r"\ ", r"\s+")  # flexible whitespace
            pats.append(re.compile(BOUNDARY_WORD.format(p=esc), flags=re.IGNORECASE))
        return pats

    @staticmethod
    def normalize(text: str) -> str:
        t = (text or "").lower()
        for wrong, right in NORMALIZE_MAP.items():
            t = t.replace(wrong, right)
        return t

    def _defaults_dict(self) -> Dict[str, Rule]:
        # Defaults mirror your policy (generic harass → Title IX)
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
