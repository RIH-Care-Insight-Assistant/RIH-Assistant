# Purpose: Load routing rules from safety/routing_matrix.csv (if present),
if not self.csv_path.exists():
return False
with self.csv_path.open(newline='', encoding='utf-8') as f:
reader = csv.DictReader(f)
rows = list(reader)
if not rows:
return False
for row in rows:
category = (row.get("category") or "").strip()
if not category:
continue
response_key = (row.get("response_key") or category).strip()
priority = int((row.get("priority") or 100))
raw_triggers = (row.get("example_triggers") or "").strip()
terms = [s.strip() for s in re.split(r"[|,]", raw_triggers) if s.strip()]
pats = self._compile_terms(terms)
self.by_category[category] = Rule(category, response_key, pats, priority)
return True


def _load_defaults(self) -> None:
# These match your previous safety_router.py behavior:
SLANG_URGENCY = [r"\bkms\b", r"\bunalive\b"]
PHRASES_URGENCY = [
r"\bkill myself\b", r"\bsuicide\b", r"\bend it\b",
r"\bhurt (myself|others)\b", r"\btake my life\b", r"\bno reason to live\b",
]
TITLE_IX = [
r"\bsex(ual)?\s*(assault|harass(ed|ment|ing)?|misconduct|coercion)\b",
r"\bharass(ed|ment|ing)?\b", # per policy: generic harass → Title IX
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


defaults = {
"urgent_safety": ("crisis", SLANG_URGENCY + PHRASES_URGENCY, 1),
"title_ix": ("title_ix", TITLE_IX, 2),
"harassment_hate": ("conduct", CONDUCT, 3),
"retention_withdraw": ("retention", RETENTION, 4),
"counseling": ("counseling", COUNSELING, 5),
}
for cat, (resp, terms, prio) in defaults.items():
self.by_category[cat] = Rule(cat, resp, [re.compile("|".join(terms), re.I)], prio)


def _load(self) -> None:
if not self._load_from_csv():
self._load_defaults()


def match(self, text: str) -> Tuple[str | None, str | None]:
"""Return (category, response_key) if matched else (None, None). Priority ascending."""
t = self.normalize(text)
for rule in sorted(self.by_category.values(), key=lambda r: r.priority):
for pat in rule.patterns:
if pat.search(t):
return rule.category, rule.response_key
return None, None
