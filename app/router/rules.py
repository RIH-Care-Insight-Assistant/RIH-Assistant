# app/router/rules.py
# Purpose: Load routing rules from safety/routing_matrix.csv (if present).
# Otherwise fall back to safe built-in defaults (including routing generic harass* appropriately).
# Patch notes:
#  - Compile triggers with flexible whitespace AND optional hyphens (matches 'nonconsensual' & 'non-consensual').
#  - Merge CSV patterns with defaults per category (CSV augments, not replaces).
#  - Support legacy CSV headers (level/auto_reply_key) and ;|, delimiters.
#  - C1/Phase 1: broader crisis + Title IX coverage (inflections, passive ideation,
#    self-harm, harm to others) and a second "skeleton" view of the text that undoes
#    common obfuscation (zero-width chars, homoglyphs, leetspeak, s p a c e d letters).
#    Negation does NOT suppress crisis routing (fail-safe); see docs/safety/crisis-routing.md.
#  - C1 review (PR #4): self-directed "hate myself/my life/my body" -> counseling, not conduct;
#    "transfer" is retention only when not about records/insurance/prescriptions. The CSV no
#    longer lists bare "hate"/"transfer", because CSV triggers cannot carry these exclusions.

from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Pattern, Tuple

CSV_PATH = Path(__file__).resolve().parents[2] / "safety" / "routing_matrix.csv"

# Word boundary that avoids matching inside tokens; {p} will be replaced by the pattern
BOUNDARY_WORD = r"(?<![A-Za-z0-9_]){p}(?![A-Za-z0-9_])"


# ---------------------------------------
# Normalization map (EDA-informed)
# ---------------------------------------
NORMALIZE_MAP = {
    # Title IX / harassment variants
    "harrased": "harassed",
    "harrassed": "harassed",
    "harrasment": "harassment",
    "harrassment": "harassment",
    "non consensual": "non-consensual",
    "title 9": "title ix",

    # Safety variants
    "unalive": "kill myself",
    "kms": "kill myself",
    "kys": "kill myself",
    "sucide": "suicide",
    "commited suicide": "committed suicide",

    # Retention phrasing
    "drop from college": "drop out",
    "leave uni": "leave university",
    "stop out": "stop out",  # keep canonical spacing

    # Counseling / scheduling variants
    "counselling": "counseling",
    "reshedule": "reschedule",
    "no show": "no-show",
    "after hours": "after-hours",
    "executive functioning": "executive-functioning",

    # Relationship / identity variants (student-voice)
    "room mate": "roommate",
    "bf/gf": "relationship",
    "break up": "breakup",
    "post traumatic stress": "ptsd",
    "o.c.d.": "ocd",
    "a.d.h.d.": "adhd",
    "impostor syndrome": "imposter syndrome",
    "coming out": "coming-out",
    "first gen": "first-gen",
}


# ---------------------------------------
# Obfuscation-resistant "skeleton" view (used IN ADDITION to normalize(), never instead)
# ---------------------------------------
# Invisible characters that can split a trigger word without changing how it looks.
_INVISIBLE_RE = re.compile("[­᠎​-‏⁠-⁤﻿]")

# Common Cyrillic/Greek look-alikes of Latin letters.
_HOMOGLYPHS = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x",
    "і": "i", "ј": "j", "ѕ": "s", "ԁ": "d", "ӏ": "l", "ɩ": "i",
    "α": "a", "ε": "e", "ι": "i", "κ": "k", "ο": "o", "ρ": "p", "τ": "t", "υ": "u", "ν": "v",
})

# Leetspeak digits/symbols. Only applied to the skeleton view, so ordinary numbers
# in the normal view (dates, phone numbers) are unaffected.
_LEET = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t",
    "@": "a", "$": "s", "!": "i", "|": "l",
})

# Three or more single letters separated by a space/dot/dash/underscore/asterisk:
# "k i l l", "s.u.i.c.i.d.e" -> joined back into one word.
_SPACED_LETTERS_RE = re.compile(r"\b(?:[a-z][\s.\-_*]){2,}[a-z]\b")


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
        """
        Compile terms into boundary-aware regexes, allowing:
          - flexible whitespace between tokens
          - OPTIONAL hyphens inside tokens (so 'nonconsensual' matches 'non-consensual')
        """
        pats: List[Pattern] = []
        for t in terms:
            t = t.strip()
            if not t:
                continue
            esc = re.escape(t)

            # Allow flexible whitespace for spaces:
            esc = esc.replace(r"\ ", r"\s+")

            # Make hyphens optional and tolerant of spaces/hyphens:
            # turn '\-' into '[-\s]*' so both 'nonconsensual' and 'non-consensual' match a 'non-consensual' trigger (and vice versa)
            esc = esc.replace(r"\-", r"[-\s]*")

            pats.append(re.compile(BOUNDARY_WORD.format(p=esc), flags=re.IGNORECASE))
        return pats

    @staticmethod
    def normalize(text: str) -> str:
        """Lowercase + targeted replacements (no heavy stemming/stopwording to preserve policy phrases)."""
        t = (text or "").lower()
        # Normalize unicode dashes to hyphen to keep tokens consistent
        t = re.sub(r"[\u2010-\u2015\u2212]", "-", t)
        # Apply known variant → canonical mappings
        for wrong, right in NORMALIZE_MAP.items():
            t = re.sub(rf"(?<!\w){re.escape(wrong)}(?!\w)", right, t)
        # Collapse whitespace
        t = re.sub(r"\s{2,}", " ", t).strip()
        return t

    @classmethod
    def skeleton(cls, text: str, *, invisible_as_space: bool = False) -> str:
        """
        Secondary matching view that undoes common obfuscation of trigger words:
        NFKC (full-width letters), invisible characters, homoglyphs, leetspeak and
        single letters separated by spaces/punctuation. Matching on this view can only
        ADD routes (match() checks all views), so it never weakens the normal view.

        invisible_as_space: treat invisible characters as word separators
        ("kill<ZWSP>myself") instead of deleting them ("ki<ZWSP>ll myself").
        """
        t = unicodedata.normalize("NFKC", text or "")
        t = _INVISIBLE_RE.sub(" " if invisible_as_space else "", t)
        t = t.lower().translate(_HOMOGLYPHS).translate(_LEET)
        t = _SPACED_LETTERS_RE.sub(lambda m: re.sub(r"[\s.\-_*]", "", m.group(0)), t)
        return cls.normalize(t)

    # -------------------------
    # Safe defaults
    # -------------------------
    def _defaults_dict(self) -> Dict[str, Rule]:
        SLANG_URGENCY = [r"\bkms\b", r"\bunalive\b", r"\bkys\b"]
        PHRASES_URGENCY = [
            r"\bkill\s+myself\b", r"\bsuicide\b", r"\bend\s+it\b",
            r"\bhurt\s+(myself|others)\b", r"\btake\s+my\s+life\b", r"\bno\s+reason\s+to\s+live\b",
        ]

        # Phase 1 (C1): suicidal ideation incl. passive ideation and inflections.
        # Deliberately caution-biased: idioms like "this exam makes me want to die" route
        # to crisis too (documented false positive; the crisis template is conditional).
        SUICIDAL_IDEATION = [
            r"\bsuicid(e|es|al|ality)\b",
            r"\bkill(ing|ed)?\s*my\s*self\b",
            r"\b(end|ending|take|taking)\s+my\s+(own\s+)?life\b",
            r"\bend(ing)?\s+it\s+all\b",
            r"\b(want(s|ed)?|wanting)\s+to\s+die\b", r"\bwanna\s+die\b",
            r"\bwish(ing)?\s+i\s+(was|were|could\s+be)\s+dead\b", r"\bwish(ing)?\s+i\s+could\s+die\b",
            r"\bbetter\s+off\s+(dead|without\s+me)\b",
            r"\b(do\s+not|don'?t|dont|no\s+longer)\s+want\s+to\s+(live|be\s+alive|exist|be\s+here|wake\s+up)\b",
            r"\bno\s+(reason|point)\s+(to|in)\s+(live|living|go(ing)?\s+on)\b",
            r"\b(not|isn'?t|ain'?t)\s+worth\s+living\b",
            r"\bcan'?t\s+go\s+on\s+(anymore|any\s+more|living|like\s+this)\b",
        ]

        SELF_HARM = [
            r"\bself[\s-]*harm(s|ed|ing)?\b",
            r"\bself[\s-]*injur(y|e|ed|ing|ious)\b",
            r"\bhurt(s|ing)?\s+my\s*self\b",
            r"\b(cut|cutting|burn|burning|hang|hanging|shoot|shooting|stab|stabbing|"
            r"drown|drowning|poison|poisoning|starve|starving)\s+my\s*self\b",
            r"\b(cut|cutting|slit|slitting)\s+my\s+(wrists?|arms?|legs?|thighs?|skin|throat)\b",
            r"\boverdos(e|ed|es|ing)\b",
            r"\btake\s+all\s+(of\s+)?my\s+(pills|meds|medications?)\b",
            r"\bjump(ing)?\s+off\s+(of\s+)?(a|the|my)\s+(\w+\s+)?(bridge|building|roof|garage|balcony|cliff|ledge)\b",
        ]

        HARM_TO_OTHERS = [
            r"\bhurt(ing)?\s+(others|someone|somebody|people|anyone|everyone)\b",
            r"\b(kill|killing|murder|murdering|stab|stabbing)\s+(someone|somebody|people|everyone|"
            r"him|her|them|my\s+(roommate|professor|teacher|ex|partner|boyfriend|girlfriend|"
            r"mom|mother|dad|father|family|classmates?))\b",
            r"\b(shoot|shooting)\s+(someone|somebody|people|everyone)\b",
            r"\bshoot\s+up\s+(the|a|my)?\s*(school|campus|class|dorm|building)\b",
        ]

        TITLE_IX = [
            r"\bsex(ual)?\s*(assault|harass(ed|ment|ing)?|misconduct|coercion)\b",
            r"\bharass(ed|ment|ing)?\b",
            r"\b(non\s*-?\s*consensual|nonconsensual)\b",
            r"\brape\b", r"\bstalk(ing)?\b",
            r"\bsupportive\s+measures\b",
            r"\bconfidential\s+advocate\b",
            # Phase 1 (C1): inflections and related Title IX conduct the base list missed
            # ("sexually assaulted", "raped", "stalked", "assaulted").
            r"\bsexual(ly)?\s+(assault(ed|ing)?|harass(ed|ment|ing)?|abuse(d)?|"
            r"exploit(ed|ation)?|coerc(ed|ion)|violence)\b",
            r"\bassault(s|ed|ing)?\b",
            r"\brap(ed|es|ing|ist)\b",
            r"\bstalk(s|ed|er|ers)\b",
            r"\bmolest(ed|ing|ation)?\b", r"\bgrop(e|ed|es|ing)\b",
            r"\bcoerc(ed|ion)\b",
            r"\bwithout\s+(my\s+)?consent\b",
            r"\b(dating|domestic|relationship|intimate\s+partner)\s+(violence|abuse)\b",
            r"\bsextortion\b", r"\brevenge\s+porn\b",
        ]

        # Self-directed distress ("I hate myself / my life / my body") is not a conduct
        # report; it is excluded here and routed to counseling below (C1 review, PR #4).
        SELF_DIRECTED = r"(?:my\s*self|my\s+(?:life|body))\b"

        CONDUCT = [
            r"\bslur\b", r"\bhate\b(?!\s+" + SELF_DIRECTED + r")", r"\bracist\b", r"\bhomophobic\b", r"\bableist\b",
            r"\bslurs\b", r"\bthreatened\b", r"\bbull(ied|ies)\b", r"\bintimidated\b",
            r"\bthreat(s|en|ening)?\b", r"\bbully(ing)?\b", r"\bintimidat(e|ion|ing)?\b",
            r"\bdoxx(ing)?\b", r"\bbias\s+incident\b", r"\btargeted\s+harassment\b", r"\bdiscrimination\b",
        ]

        RETENTION = [
            r"\b(withdraw(al)?|drop\s?out|leave\s+school|quit\s+college|leave\s+of\s+absence|stop\s+out)\b",
            # C1 review (PR #4): inflections, and "transfer" only when it is not about moving
            # records/insurance/prescriptions ("transfer my medical records" is not retention).
            r"\b(withdraw(ing|n)|drop(ping|ped)\s+out|leav(e|ing)\s+(school|college|umbc)|"
            r"quit(ting)?\s+(school|college)|stop(ping|ped)\s+out)\b",
            r"\btransfer(ring|red|s)?\b(?!\s+(of\s+)?(my\s+|the\s+|our\s+)?(medical\s+|health\s+|immunization\s+|"
            r"vaccin\w*\s+)?(records?|files?|insurance|prescriptions?|refills?|care|money|funds|payments?))",
        ]

        COUNSELING = [
            r"\b(counsel(ing)?|therapy|therapist|mental\s+health|talk\s+to\s+(someone|a\s+counsel(or|l)?)?)\b",
            r"\b(appointment|schedule|session|intake|reschedule|cancel)\b",
            r"\b(workshop|support\s+group|group\s+counseling)\b",
            # Self-directed distress below the crisis threshold (excluded from conduct above).
            r"\bhate\s+" + SELF_DIRECTED,
        ]

        return {
            "urgent_safety": Rule("urgent_safety", "crisis",
                                  [re.compile("|".join(SLANG_URGENCY + PHRASES_URGENCY + SUICIDAL_IDEATION
                                                       + SELF_HARM + HARM_TO_OTHERS), re.I)], 1),
            "title_ix": Rule("title_ix", "title_ix", [re.compile("|".join(TITLE_IX), re.I)], 2),
            "harassment_hate": Rule("harassment_hate", "conduct", [re.compile("|".join(CONDUCT), re.I)], 3),
            "retention_withdraw": Rule("retention_withdraw", "retention", [re.compile("|".join(RETENTION), re.I)], 4),
            "counseling": Rule("counseling", "counseling", [re.compile("|".join(COUNSELING), re.I)], 5),
        }

    # -------------------------
    # CSV loader (legacy + new)
    # -------------------------
    def _load_from_csv(self) -> Dict[str, Rule]:
        """
        Load rules from safety/routing_matrix.csv.

        Supports BOTH schemas:
          - Legacy:
              level, example_triggers, auto_reply_key, destination, sla, after_hours
          - New:
              category, example_triggers, response_key, priority, ...

        Trigger delimiters supported: ';'  '|'  ','  (any of them).
        """
        rules: Dict[str, Rule] = {}
        if not self.csv_path.exists():
            return rules

        def _split_triggers(s: str) -> List[str]:
            return [t.strip() for t in re.split(r"[;|,]", s or "") if t.strip()]

        with self.csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                category = (row.get("category") or row.get("level") or "").strip()
                if not category:
                    continue
                response_key = (row.get("response_key") or row.get("auto_reply_key") or category).strip()

                pri_raw = (row.get("priority") or "").strip()
                try:
                    priority = int(pri_raw) if pri_raw else {
                        "urgent_safety": 1,
                        "title_ix": 2,
                        "harassment_hate": 3,
                        "retention_withdraw": 4,
                        "counseling": 5,
                    }.get(category, 100)
                except ValueError:
                    priority = 100

                raw_triggers = (row.get("example_triggers") or "").strip()
                terms = _split_triggers(raw_triggers)
                pats = self._compile_terms(terms) if terms else []

                if pats:
                    # MERGE: if category already exists (from defaults), extend patterns instead of replacing
                    if category in rules:
                        rules[category].patterns.extend(pats)
                        # keep the lower priority of the two (CSV can change it explicitly)
                        rules[category].priority = min(rules[category].priority, priority)
                        # response_key: prefer explicit CSV value if provided
                        rules[category].response_key = response_key or rules[category].response_key
                    else:
                        rules[category] = Rule(category, response_key, pats, priority)

        return rules

    # -------------------------
    # Merge + expose
    # -------------------------
    def _load(self) -> None:
        """Merge defaults with CSV rules (CSV augments/overrides fields, but keeps default patterns too)."""
        defaults = self._defaults_dict()
        csv_rules = self._load_from_csv()  # may be partial

        merged: Dict[str, Rule] = {}

        # start from defaults
        for cat, rule in defaults.items():
            merged[cat] = Rule(cat, rule.response_key, list(rule.patterns), rule.priority)

        # augment with CSV: extend patterns & allow response_key/priority overrides
        for cat, csv_rule in csv_rules.items():
            if cat in merged:
                merged[cat].patterns.extend(csv_rule.patterns)
                merged[cat].response_key = csv_rule.response_key or merged[cat].response_key
                merged[cat].priority = min(merged[cat].priority, csv_rule.priority)
            else:
                merged[cat] = csv_rule

        self.by_category = merged

    def match(self, text: str) -> Tuple[str | None, str | None]:
        """
        Return (category, response_key) if matched else (None, None).

        Rules are evaluated strictly in priority order; for each rule both the
        normalized text and the de-obfuscated skeleton are checked, so a lower-priority
        match on the normal view can never pre-empt a higher-priority match on the skeleton.
        """
        views = [self.normalize(text)]
        for skel in (self.skeleton(text), self.skeleton(text, invisible_as_space=True)):
            if skel not in views:
                views.append(skel)
        for rule in sorted(self.by_category.values(), key=lambda r: r.priority):
            for pat in rule.patterns:
                if any(pat.search(v) for v in views):
                    return rule.category, rule.response_key
        return None, None
