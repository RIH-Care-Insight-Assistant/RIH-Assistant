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
#  - C1 B9 repair: Devika's held-out check missed whole phrasing families, not single phrases.
#    Added: someone else's suicide/self-harm, "harm myself", overdose without the word,
#    unwanted sexual contact/messages and coerced sex, bias-motivated mockery, and threats
#    or attacks against the student. See docs/safety/crisis-routing.md §2.

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
# Apostrophe look-alikes: curly quotes (default on iOS/macOS), modifier letters, prime,
# acute accent, backtick, full-width. Used by normalize(), so it applies to every view.
APOSTROPHE_VARIANTS = "\u2018\u2019\u201a\u201b\u02b9\u02bb\u02bc\u2032\u00b4`\uff07"
_APOSTROPHES_RE = re.compile("[" + re.escape(APOSTROPHE_VARIANTS) + "]")

# Invisible characters that can split a trigger word without changing how it looks.
_INVISIBLE_RE = re.compile("[\u00ad\u180e\u200b-\u200f\u2060-\u2064\ufeff]")

# Common Cyrillic/Greek look-alikes of Latin letters.
_HOMOGLYPHS = str.maketrans({
    "\u0430": "a", "\u0435": "e", "\u043e": "o", "\u0440": "p", "\u0441": "c", "\u0443": "y", "\u0445": "x",
    "\u0456": "i", "\u0458": "j", "\u0455": "s", "\u0501": "d", "\u04cf": "l", "\u0269": "i",
    "\u03b1": "a", "\u03b5": "e", "\u03b9": "i", "\u03ba": "k", "\u03bf": "o", "\u03c1": "p", "\u03c4": "t", "\u03c5": "u", "\u03bd": "v",
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
        # Normalize apostrophe look-alikes to "'" so contractions in triggers ("don't",
        # "can't", "isn't") also match "smart" punctuation typed on phones and Macs.
        t = _APOSTROPHES_RE.sub("'", t)
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
            r"\bharm(s|ed|ing)?\s+my\s*self\b",
            r"\b(cut|cutting|burn|burning|hang|hanging|shoot|shooting|stab|stabbing|"
            r"drown|drowning|poison|poisoning|starve|starving)\s+my\s*self\b",
            r"\b(cut|cutting|slit|slitting)\s+my\s+(wrists?|arms?|legs?|thighs?|skin|throat)\b",
            r"\boverdos(e|ed|es|ing)\b",
            # PR #12 review (M02): following directions ("take all my medications as prescribed")
            # is not an overdose; the lookahead only removes that one phrase.
            r"\btake\s+all\s+(of\s+)?my\s+(pills|meds|medications?)\b"
            r"(?!\s+(as\s+(prescribed|directed|instructed)|every\s+(day|morning|night)|daily|on\s+time|with\s+food)\b)",
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

        # C1 B9: risk to someone else ("my friend wants to kill herself"). The reflexive must
        # not be the start of "self-esteem" and similar compounds.
        REFLEXIVE_OTHER = (r"(?:them\s*selves|them\s*self|him\s*self|her\s*self|your\s*self|your\s*selves)"
                           r"(?![\s-]*(?:esteem|image|confidence|worth|respect|care|awareness)\b)")
        THIRD_PARTY_RISK = [
            r"\bkill(s|ed|ing)?\s+" + REFLEXIVE_OTHER,
            r"\b(end|ends|ended|ending|take|takes|took|taking)\s+(his|her|their)\s+(own\s+)?li(fe|ves)\b",
            r"\b(cut|cuts|cutting|burn|burns|burning|hang|hangs|hanging|starv(e|es|ing)|poison(s|ing)?|"
            r"drown(s|ing)?|shoot(s|ing)?|stab(s|bing)?)\s+" + REFLEXIVE_OTHER,
            # "hurt/harm themselves" needs intent or ongoing wording, so an accident
            # ("she hurt herself playing soccer", "might have hurt himself") is not crisis.
            r"\b(going\s+to|gonna|wants?\s+to|wanted\s+to|wanting\s+to|will|'ll|would|'d|might|"
            r"plans?\s+to|planning\s+to|planned\s+to|threaten(s|ed|ing)?\s+to|tr(y|ies|ied|ying)\s+to|"
            r"talk(s|ed|ing)?\s+about|think(s|ing)?\s+(about|of))\s+"
            r"(?:(?!have\b|has\b|had\b)\w+\s+){0,2}(hurt(ing)?|harm(ing)?)\s+" + REFLEXIVE_OTHER,
            r"\b(hurting|harming)\s+" + REFLEXIVE_OTHER,
        ]

        # C1 B9: overdose or poisoning described without the word "overdose"
        # ("swallowed a bottle of pills"). A quantity or "all/too many" is required, so
        # taking a normal dose ("I took my pills this morning") does not match.
        PILLS = (r"(pills?|tablets?|capsules?|meds|medications?|medicines?|painkillers?|"
                 r"tylenol|advil|ibuprofen|acetaminophen|paracetamol|aspirin|benadryl|xanax|insulin)\b")
        # PR #12 review (M01, M03): "take/took" also means carrying ("took a bottle of pills to
        # the pharmacy", "take a pack of tablets in my carry-on"). Only for take/took, a
        # destination or travel phrase right after the medication means transport. Swallow,
        # ate, popped etc. are always ingestion, and a separate overdose clause still matches.
        TRANSPORT = (r"(?!\s+(to|into|in|on|onto|through|at)\s+((the|a|an|my|his|her|their|campus|local|nearest|student)\s+){0,2}"
                     r"(pharmacy|pharmacist|clinic|health\s+center|rih|doctor'?s?|nurse'?s?|office|airport|plane|flight|"
                     r"bag|luggage|carry-?on|suitcase|backpack|purse|trip|drop-?off|disposal|drop\s+box|take-?back)\b"
                     r"|\s+for\s+(disposal|recycling|travel|(my|the|a)\s+trip)\b|\s+back\s+to\b)")
        TAKE = r"\b(took|taken|tak(e|es|ing))"
        INGEST = r"\b(swallow(s|ed|ing)?|ate|eat(s|en|ing)?|pop(s|ped|ping)?|downed|chug(s|ged|ging)?)"
        QUANTITY = (r"\s+((a|an|the|my|his|her|their|half\s+(a|the|my))\s+)?(whole\s+|entire\s+|full\s+)?"
                    r"(bottles?|packs?|packets?|box(es)?|handfuls?|bunch|lots?|strips?|blister\s+packs?)\s+of\s+"
                    r"([\w-]+\s+)?" + PILLS)
        TOO_MANY = r"\s+(\w+\s+)?too\s+(many|much)\s+([\w-]+\s+)?" + PILLS
        ALL_OF = r"\s+all\s+(of\s+)?(my|his|her|their|the)\s+([\w-]+\s+)?" + PILLS
        INGESTION = [
            INGEST + QUANTITY, TAKE + QUANTITY + TRANSPORT,
            INGEST + TOO_MANY, TAKE + TOO_MANY + TRANSPORT,
            INGEST + ALL_OF,
            TAKE + ALL_OF + TRANSPORT
            + r"(?!\s+(as\s+(prescribed|directed|instructed)|every\s+(day|morning|night)|daily|on\s+time|with\s+food)\b)",
            r"\b(drank|drink(s|ing)?|swallow(s|ed|ing)?|ingest(s|ed|ing)?)\s+(some\s+|a\s+lot\s+of\s+)?"
            r"(bleach|antifreeze|rat\s+poison|drain\s+cleaner|poison|weed\s*killer|pesticides?)\b",
        ]

        # PR #12 review, policy approved by both: explicit reported threats or attempts to kill,
        # shoot, stab or strangle anyone (the student or a third party), weapon threats and
        # active shootings get urgent guidance (911, UMBC Police) before Title IX or conduct.
        # The router does not judge credibility. It needs a reported threat, a person as the
        # subject, or an attempt, so idioms ("this homework is going to kill me", "shoot me an
        # email", "stabbed me in the back", "hit him up") do not match. Beatings and punches
        # stay conduct.
        SEVERE = r"(kill|murder|shoot|stab|strangle|choke|slit\s+\w+\s+throat)"
        PERSON = (r"(student|guy|man|woman|person|people|professor|teacher|instructor|ta|kid|girl|boy|roommates?|"
                  r"neighbou?rs?|officer|classmates?|friends?|partner|boyfriend|girlfriend|ex|husband|wife|sister|brother|"
                  r"mom|mother|dad|father|parents|family|kids|child|children|son|daughter|teammates?|advisor|coworkers?|"
                  r"boss|suitemates?|housemates?)")
        VICTIM = (r"(me|us|you|him|her|them|everyone|everybody|someone|somebody|people|"
                  r"(my|our|his|her|their|the|a|an|that|this)\s+" + PERSON + r")\b")
        WEAPON = r"(guns?|pistol|rifle|firearm|handgun|knife|knives|blade|machete|weapons?)"
        SEVERE_THREAT = [
            r"\bthreat(en|ens|ened|ening)\s+(\w+\s+){0,3}?to\s+" + SEVERE + r"\s+" + VICTIM,
            r"\b(promis|vow|swear|swore|sworn|warn)\w*\s+(that\s+)?(\w+\s+){0,2}?(to|'ll|will|would|gonna|going\s+to)\s+"
            + SEVERE + r"\s+" + VICTIM,
            # Reported speech: "said he will kill me", "texted that they will shoot my roommate".
            r"\b(said|says|saying|told|tells|telling|text(s|ed|ing)?|messag(es|ed|ing)|wrote|writes|posted|posts|"
            r"yell(s|ed|ing)|shout(s|ed|ing)|scream(s|ed|ing))\s+((me|us|him|her|them|my\s+\w+)\s+)?"
            r"(that\s+|[:\"']\s*)?(he|she|they|someone|somebody|people|everyone|i|we)\s*"
            r"('ll|'d|'s\s+going\s+to|'re\s+going\s+to|'m\s+going\s+to|\s+will|\s+would|\s+gonna|"
            r"\s+(is|are|was|were|am)\s+(going\s+to|gonna|planning\s+to)|\s+plans?\s+to|\s+wants?\s+to)\s+"
            + SEVERE + r"\s+" + VICTIM,
            # A person as the subject. Family and roommates are left out here because "my mom is
            # going to kill me" is usually an idiom; a reported threat from anyone still matches above.
            r"\b(he|she|someone|somebody|(a|an|the|this|that|my|our)\s+(stranger|student|guy|man|woman|person|group|"
            r"ex|partner|boyfriend|girlfriend|husband|wife|stalker))\s*('s|\s+is|\s+was)?\s*"
            r"(going\s+to|gonna|trying\s+to|tried\s+to|wants?\s+to|wanted\s+to|plans?\s+to|planning\s+to|will|'ll)\s+"
            + SEVERE + r"\s+" + VICTIM,
            r"\bthey('re|\s+are|\s+were)?\s+(trying\s+to|tried\s+to|wants?\s+to|wanted\s+to|plans?\s+to|planning\s+to)\s+"
            + SEVERE + r"\s+" + VICTIM,
            # Attempted or in-progress severe violence.
            r"\b(tried|tries|trying|attempted|attempting)\s+to\s+" + SEVERE + r"\s+" + VICTIM,
            # In progress, with a person as the subject. "killing" is left out ("this deadline is
            # killing me") and "shooting me a look" is excluded.
            r"\b(he|she|they|someone|somebody|(a|an|the|my|our|this|that)\s+(stranger|" + PERSON[1:]
            + r")\s*(is|are|was|were|'s|'re)\s+(stabbing|shooting|strangling|choking)\s+" + VICTIM + r"(?!\s+(a|an)\s)",
            r"\b(stabbed|strangled|choked)\s+" + VICTIM + r"(?!\s+in\s+the\s+back)",
            r"\bshot\s+(at\s+)?" + VICTIM + r"(?!\s+(a|an)\s)",
            # Weapons.
            r"\b(pulled|pointed|aimed|waved|brandished|flashed|drew)\s+(a|an|his|her|their|the)\s+" + WEAPON + r"\b",
            r"\b(threaten\w*|attack\w*|chas(ed|ing)|came\s+at|charged\s+at|swung\s+at|hit|stabbed|shot|cut|jumped)\s+"
            r"(\w+\s+){0,3}?with\s+(a|an|his|her|their)\s+" + WEAPON + r"\b",
            r"\b(someone|somebody|a\s+(man|guy|person|student|stranger|woman)|there'?s\s+(a|an)\s+\w+|there\s+is\s+"
            r"(a|an|someone)(\s+\w+)?)\s+(\w+\s+){0,4}?with\s+(a|an)\s+" + WEAPON + r"\b",
            r"\bactive\s+shooter\b", r"\bshots\s+(were\s+)?fired\b",
            r"\b(someone|somebody|a\s+\w+)\s+(is|was)\s+shooting\b"
            r"(?!\s+(a|the|some|my|our)\s+(video|film|photos?|movie|scene|hoops|baskets|pool|project))",
        ]

        # PR #12 review, policy approved by both: harassment with no sexual or sex-based signal
        # routes to conduct (CONDUCT below), not Title IX. Sexual and sex/gender-based
        # harassment, stalking and dating/domestic violence stay Title IX.
        TITLE_IX = [
            r"\bsex(ual)?\s*(assault|harass(ed|ment|ing)?|misconduct|coercion)\b",
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

        # PR #12 review (B01-B04): a few Title IX patterns also describe consented care or
        # health education ("touched my chest during an exam I agreed to", "how to discuss
        # sexual messages with a partner"). Such a pattern is skipped only when the SAME clause
        # has a consent/information context AND no harm marker, so a benign phrase can never
        # cancel an unwanted, forced or exploitative event. There is no blanket clinician,
        # class or workshop exemption.
        def unless_benign(core: str, benign: str) -> str:
            clause = r"[^.;!?]*"
            return (r"(?:^|(?<=[.;!?]))(?!(?=" + clause + benign + r")(?!" + clause + SEXUAL_HARM + r"))"
                    + clause + core)

        SEXUAL_HARM = (r"\b(unwanted|without\s+((my|their|his|her|our)\s+)?(consent|permission|agreement)|"
                       r"against\s+(my|their|his|her)\s+will|forc\w*|pressur\w*|coerc\w*|blackmail\w*|threat\w*|"
                       r"leak\w*|(didn'?t|did\s+not|never)\s+(agree|consent|want|ask)|"
                       r"(said|told\s+\w+)\s+(no|stop|not\s+to)|won'?t\s+stop|wouldn'?t\s+stop|kept|keeps|"
                       r"asleep|unconscious|passed\s+out|for\s+a\s+(better\s+)?grade|in\s+exchange|or\s+else|"
                       r"(sent|sends|send(ing)?|show(s|ed|ing)?|text(s|ed|ing)?|messag(es|ed|ing))\s+(me|us)|"
                       r"(to|at|about|of)\s+(me|us))\b")
        CONSENT_CONTEXT = (r"\b((that\s+)?i\s+(agreed|consented)\s+to|with\s+(my|their|our)\s+(permission|consent|agreement)|"
                           r"by\s+mutual\s+(agreement|consent)|mutually\s+agreed|consensual(ly)?|"
                           r"we\s+both\s+(agreed|consented|wanted))\b")
        INFO_CONTEXT = (r"\b(how\s+to|how\s+do|how\s+can|information\s+(about|on)|info\s+(about|on)|"
                        r"learn(ing)?\s+(about|how)|discuss(ing)?|talk(ing)?\s+about|explain(s|ed|ing)?|"
                        r"tips\s+(on|for)|safely|safer|guidance\s+on|resources?\s+(on|about)|policy\s+on|"
                        r"what\s+(is|are|counts\s+as))\b")
        BENIGN_SEXUAL_CONTEXT = "(" + CONSENT_CONTEXT + "|" + INFO_CONTEXT + ")"

        # Sex- or gender-based mistreatment ("harassing me because I am a woman").
        SEX_TERM = (r"((my|our|her|his|their)\s+(gender(\s+identity)?|sex|pregnancy)|"
                    r"((i'?m|i\s+am|we'?re|we\s+are|being|(s?he|they)'?s|(s?he|they)\s+(is|are))\s+)?(an?\s+)?"
                    r"(woman|girl|man|guy|female|male|trans(gender)?|non[\s-]*binary|pregnant|intersex))\b")
        SEX_BASED = [
            r"\b(harass\w*|bull(y|ies|ied|ying)|threat\w*|discriminat\w*|mock\w*|insult\w*|target\w*|exclud\w*|"
            r"pick(s|ed|ing)?\s+on|(make|makes|made|making)\s+fun\s+of)\b([\s,]+[\w']+){0,6}?[\s,]+"
            r"(because\s+(of\s+)?|for\s+(being\s+)?|over\s+|about\s+|since\s+)" + SEX_TERM,
            r"\b(harass\w*|mock\w*|insult\w*|ridicul\w*)\s+(my|our|her|his|their)\s+(gender(\s+identity)?|pregnancy)\b",
            r"\b(sex|gender)[\s-]*(based\s+)?(harassment|discrimination|bias)\b",
            r"\bsexis[tm]\b",
        ]

        # C1 B9: sexual misconduct described without "assault"/"harassment"/"consent".
        # Health wording ("sexual health", "unprotected sex", "sexual orientation") stays out:
        # every pattern needs an unwanted, forced or explicit element.
        SEXUAL_MISCONDUCT = [
            r"\bunwanted\s+(sexual\w*|sex|touch(es|ed|ing)?|kiss(es|ed|ing)?|advances?|groping|nudes?|"
            r"explicit\s+\w+|(dick|nude|explicit)\s+pics?)\b",
            unless_benign(r"\bsexual(ly)?\s+(explicit|suggestive|inappropriate)\b", BENIGN_SEXUAL_CONTEXT),
            unless_benign(r"\bsexual\s+(messages?|texts?|comments?|remarks?|jokes?|advances?|propositions?|favou?rs?|"
                          r"requests?|innuendos?|gestures?|photos?|pictures?|pics|images?|videos?|touching)\b",
                          BENIGN_SEXUAL_CONTEXT),
            r"\b(inappropriate(ly)?|sexually)\s+touch(es|ed|ing)?\b",
            r"\btouch(es|ed|ing)?\s+(me|my\s+[\w-]+)\s+(sexually|inappropriately|without\s+(my\s+)?(consent|permission))\b",
            r"\b(kiss(es|ed|ing)?|touch(es|ed|ing)?|grabb?(s|ed|ing)?|fondl(e|es|ed|ing))\s+(me|my\s+[\w-]+)\s+"
            r"(\w+\s+){0,6}?(after|when|even\s+(though|after|when)|although|though)\s+i\s+"
            r"(said|told\s+(him|her|them))\s+(no|stop|not\s+to)\b",
            # Only an explicit consent clause (not "clinician" or "exam" alone) can exempt this.
            unless_benign(r"\b(grabb?(s|ed|ing)?|touch(es|ed|ing)?|fondl(e|es|ed|ing)|rubb?(s|ed|ing)?)\s+(my|her|his)\s+"
                          r"(butt|ass|breasts?|boobs?|chest|crotch|genitals?|groin|privates?|private\s+parts|inner\s+thighs?)\b",
                          CONSENT_CONTEXT),
            r"\bfondl(e|es|ed|ing)\b",
            # Coerced or forced sex ("forced me into sex", "pressured me to have sex").
            r"\b(forc(e|es|ed|ing)|pressur(e|es|ed|ing)|coerc(e|es|ed|ing)|blackmail(s|ed|ing)?|"
            r"guilt[\s-]*trip(s|ped|ping)?)\s+(me|him|her|them|someone|my\s+\w+)\s+(in)?to\s+"
            r"(have\s+|having\s+)?(sex|sexual|oral|sleep\s+with|hook\s+up|send\s+nudes)",
            r"\b(made|make|makes|making)\s+me\s+(have\s+sex|do\s+sexual|perform\s+(sexual|oral)|sleep\s+with|send\s+nudes)",
            r"\bforced\s+(him|her|them)\s*sel(f|ves)\s+on(to)?\s+me\b",
            # Image-based abuse.
            r"\b(sent|send(s|ing)?|shar(e|es|ed|ing)|leak(s|ed|ing)?|post(s|ed|ing)?|spread(s|ing)?)\s+"
            r"(me\s+)?(my\s+|his\s+|her\s+|their\s+)?nudes\b",
            unless_benign(r"\b(intimate|explicit|nude)\s+(photos?|pictures?|pics|images?|videos?)\b", BENIGN_SEXUAL_CONTEXT),
        ]

        # Self-directed distress ("I hate myself / my life / my body") is not a conduct
        # report; it routes to counseling below (C1 review, PR #4). No HATE_BIAS pattern
        # matches it.
        SELF_DIRECTED = r"(?:my\s*self|my\s+(?:life|body))\b"

        # Bare "hate" is no longer a conduct trigger (O10); see HATE_BIAS below.
        CONDUCT = [
            r"\bslur\b", r"\bracist\b", r"\bhomophobic\b", r"\bableist\b",
            r"\bslurs\b", r"\bthreatened\b", r"\bbull(ied|ies)\b", r"\bintimidated\b",
            r"\bthreat(s|en|ening)?\b", r"\bbully(ing)?\b", r"\bintimidat(e|ion|ing)?\b",
            r"\bdoxx(ing)?\b", r"\bbias\s+incident\b", r"\btargeted\s+harassment\b", r"\bdiscrimination\b",
            # PR #12 review: harassment with no sexual or sex-based signal (Title IX checks first).
            r"\bharass(es|ed|ment|ing|er|ers)?\b",
        ]

        # C1 B9: hostility aimed at a protected characteristic, without "bully"/"slur"/"threat"
        # ("mocking my disability", "excluded me because I'm Muslim"). The identity term must be
        # the direct object or follow "because/for/about/over", so neither "make fun of the
        # reading" nor "laughed at the movie in my religion class" is a report.
        PROTECTED = (r"(race|racial\s+\w+|ethnicity|ethnic\s+\w+|religion|religious\s+\w+|faith|disabilit(y|ies)|"
                     r"wheelchair|gender(\s+identity)?|sexuality|sexual\s+orientation|orientation|nationality|"
                     r"national\s+origin|accent|skin(\s+colou?r)?|immigration\s+status|citizenship|hijab|turban|"
                     r"headscarf|yarmulke|kippah|pronouns|culture|heritage|caste|pregnancy)")
        IDENTITY = (r"(black|white|asian|latin[oax]|latine|hispanic|arab|jewish|muslim|christian|hindu|sikh|"
                    r"buddhist|atheist|gay|lesbian|bi(sexual)?|queer|trans(gender)?|non[\s-]*binary|intersex|"
                    r"disabled|deaf|blind|autistic|neurodivergent|immigrant|undocumented|international|foreign|"
                    r"indigenous|native|female|a\s+woman|a\s+girl|pregnant)")
        HOSTILE = (r"(mock(s|ed|ing)?|ridicul(e|es|ed|ing)|teas(e|es|ed|ing)|taunt(s|ed|ing)?|insult(s|ed|ing)?|"
                   r"demean(s|ed|ing)?|belittl(e|es|ed|ing)|humiliat(e|es|ed|ing)|(make|makes|made|making)\s+fun\s+of|"
                   r"pick(s|ed|ing)?\s+on|laugh(s|ed|ing)?\s+at|exclud(e|es|ed|ing)|ostraci[sz](e|es|ed|ing)|"
                   r"target(s|ed|ing)?|attack(s|ed|ing)?|(yell|scream|shout)(s|ed|ing)?\s+at|spit(s|ting)?\s+on|spat\s+on)")
        IDENTITY_TERM = (r"((my|our|his|her|their)\s+([\w-]+\s+)?" + PROTECTED
                         + r"|(i'?m|i\s+am|we'?re|we\s+are|being|(s?he|they)'?s|(s?he|they)\s+(is|are))\s+(an?\s+)?"
                         + IDENTITY + r")\b")
        BIAS_HOSTILITY = [
            # Direct object: "mocking my disability", "laughed at my hijab".
            r"\b" + HOSTILE + r"\s+" + IDENTITY_TERM,
            # Object, up to three words, then a reason: "excluded me because I'm gay".
            r"\b" + HOSTILE + r"\s+(me|us|him|her|them|people|everyone|someone|my\s+(friends?|roommates?|partner|"
            r"classmates?|sister|brother|kids?|child|son|daughter|girlfriend|boyfriend))\b([\s,]+[\w']+){0,3}?[\s,]+"
            r"(because\s+(of\s+)?|for\s+|over\s+|about\s+|due\s+to\s+|since\s+)" + IDENTITY_TERM,
            # A group: "mocking disabled students".
            r"\b" + HOSTILE + r"\s+(all\s+)?" + IDENTITY
            + r"\s+(people|students|folks|kids|classmates|women|men|girls|guys)\b",
            # Name-calling is bullying in itself, like "bullied".
            r"\bcall(s|ed|ing)?\s+(me|us|him|her|them|my\s+\w+)\s+(names|slurs)\b",
        ]

        # O10 (B9-N01): bare "hate" is usually everyday dislike ("I hate waiting for
        # appointments"), not a bias report. Conduct now needs hate aimed at people or a named
        # form of hate. Self-directed hate ("hate myself/my life/my body") stays counseling.
        HATE = r"\bhat(e|es|ed|ing)"
        GROUPS = (r"(muslims|jews|christians|hindus|sikhs|atheists|immigrants|foreigners|gays|lesbians|asians|blacks|"
                  r"latinos|latinas|hispanics|arabs|mexicans|indians|africans|refugees)")
        HATE_FORMS = r"(speech|groups?|messages?|mail|notes?|letters?|comments?|posts?|attacks?|signs?|words|threats?)"
        # PR #12 review (H01-H03): any inflection of a reporting verb, with or without a
        # recipient ("sent me hate messages", "keeps sending hate messages", "is posting hate
        # speech"). After "I hate" these words stay a verb and its object.
        REPORT_VERB = (r"(send(s|ing)?|sent|writ(e|es|ing|ten)|wrote|post(s|ed|ing)?|leav(e|es|ing)|left|"
                       r"spread(s|ing)?|receiv(e|es|ed|ing)|get(s|ting)?|got(ten)?|find(s|ing)?|found|"
                       r"shout(s|ed|ing)?|yell(s|ed|ing)?|scrawl(s|ed|ing)?|paint(s|ed|ing)?|spray[\s-]*paint(s|ed|ing)?)")
        # Course or activity nouns: "I hate my religion homework" is not a report.
        NOT_COURSE = (r"(?!\s+(homework|class(es)?|courses?|assignments?|exams?|tests?|quiz(zes)?|papers?|essays?|"
                      r"projects?|requirements?|lectures?|seminars?|readings?|major|minor|credits?|teachers?|professors?|"
                      r"instructors?|textbooks?|notes|department|studies|program|club|presentations?|labs?|section|"
                      r"final|midterm)\b)")
        HATE_TARGET = (r"(me|us|him|her|them|people|everyone|(my|our|his|her|their)\s+([\w-]+\s+)?" + PROTECTED
                       + NOT_COURSE + r"|" + IDENTITY + r"\s+(people|students|folks|classmates)|" + GROUPS + r")\b")
        HATE_BIAS = [
            r"\bhate[\s-]*(crimes?|incidents?|symbols?|graffiti|propaganda|flyers?|literature|campaigns?|rhetoric|"
            r"violence|vandalism)\b",
            r"\b(" + REPORT_VERB + r"(\s+(me|us|him|her|them|(my|our)\s+\w+))?|a|an|the|some|any|more|of|with|is|are|"
            r"was|were|been|there's|full\s+of|filled\s+with)\s+hate[\s-]*" + HATE_FORMS + r"\b",
            # Directed hate content: "hate speech about me", "hate comments against Muslims".
            r"\bhate[\s-]*" + HATE_FORMS + r"\s+(to|about|against|toward(s)?|at|targeting|aimed\s+at|directed\s+at)\s+"
            + HATE_TARGET,
            r"\bhateful\b",
            HATE + r"\s+(on\s+)?(me|us|you|him|her|them)\b",
            # "people/everyone" only with an identity link; "I hate people interrupting me" is a dislike.
            HATE + r"\s+(people|everyone|anyone|folks)\s+(like\s+(me|us|him|her|them)|of\s+(my|our|his|her|their)\s+"
            r"([\w-]+\s+)?" + PROTECTED + r"|from\s+(my|our|his|her|their)\s+(country|culture|community))\b",
            HATE + r"\s+(on\s+)?(my|our|his|her|their)\s+(kind|people|community|identity|([\w-]+\s+)?" + PROTECTED + r")\b"
            + NOT_COURSE,
            HATE + r"\s+(all\s+)?(those\s+|these\s+|the\s+)?" + IDENTITY
            + r"\s+(people|students|folks|kids|classmates|women|men|girls|guys)\b",
            HATE + r"\s+(all\s+)?(those\s+|these\s+|the\s+)?" + GROUPS + r"\b",
        ]

        # C1 B9: threats or attacks against the student ("promising to beat me up", "punched
        # me"). Threat wording already routes to conduct; these cover threats and attacks that
        # never say "threat". Threats to kill, shoot, stab or strangle match SEVERE_THREAT
        # (urgent) first. Idioms ("this exam is going to kill me") and "hit me up" do not match.
        VIOLENCE_AT_ME = (r"((beat|attack|jump|punch|stab|shoot|kill|hurt|harm|strangle|choke)\s+(me|us)\b|"
                          r"hit\s+(me|us)\b(?!\s+up\b))")
        THREAT_OR_ATTACK = [
            r"\bbeat(s|ing)?\s+(me|us)\s+up\b", r"\bbeat\s+up\s+(me|us)\b",
            r"\b(promis|vow|swear|swore|sworn|warn)\w*\s+(that\s+)?(\w+\s+){0,2}?(to|'ll|will|would|gonna|going\s+to)\s+"
            + VIOLENCE_AT_ME,
            r"\b(said|says|saying|told\s+me|tells\s+me|telling\s+me|text(s|ed|ing)?\s+me|messag(es|ed|ing)\s+me|"
            r"wrote|posted)\s+(that\s+)?(he|she|they|someone|somebody|people|everyone)\s*"
            r"('ll|'d|'s\s+going\s+to|'re\s+going\s+to|\s+will|\s+would|\s+gonna|\s+(is|are|was|were)\s+going\s+to)\s+"
            + VIOLENCE_AT_ME,
            r"\b(someone|somebody|people|a\s+stranger|a\s+(student|guy|man|woman|person|group))\s+(is\s+|are\s+|was\s+|were\s+)?"
            r"(going\s+to|gonna|trying\s+to|tried\s+to|wants?\s+to|wanted\s+to|plans?\s+to|planning\s+to)\s+" + VIOLENCE_AT_ME,
            r"\b(he|she|they)(\s+is|\s+are|\s+was|\s+were|'s|'re)?\s+(trying\s+to|tried\s+to|wants?\s+to|wanted\s+to|"
            r"plans?\s+to|planning\s+to)\s+" + VIOLENCE_AT_ME,
            r"\b(punch(es|ed)?|kick(s|ed)?|slapp(ed)?|slaps|shov(es|ed)|chok(es|ed)|strangl(es|ed)|attack(s|ed)|jumped)\s+me\b"
            r"(?!\s+(out|off|up|in\s+line|to\s+the\s+front)\b)",
        ]

        RETENTION = [
            r"\b(withdraw(al)?|drop\s?out|leave\s+school|quit\s+college|leave\s+of\s+absence|stop\s+out)\b",
            # C1 review (PR #4): inflections, and "transfer" only when it is not about moving
            # records/insurance/prescriptions ("transfer my medical records" is not retention).
            r"\b(withdraw(ing|n)|drop(ping|ped)\s+out|leav(e|ing)\s+(school|college|umbc)|"
            r"quit(ting)?\s+(school|college)|stop(ping|ped)\s+out)\b",
            # B9-N05: any determiner and up to two describing words ("transfer an immunization
            # record", "transfer this year's vaccination records").
            r"\btransfer(ring|red|s)?\b(?!\s+(of\s+)?((a|an|the|my|our|your|his|her|their|this|that|these|those|some|"
            r"all\s+(of\s+)?my)\s+)?([\w'-]+\s+){0,2}?(records?|files?|insurance|prescriptions?|refills?|care|money|"
            r"funds|payments?)\b)",
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
                                                       + SELF_HARM + HARM_TO_OTHERS + THIRD_PARTY_RISK
                                                       + INGESTION + SEVERE_THREAT), re.I)], 1),
            "title_ix": Rule("title_ix", "title_ix",
                             [re.compile("|".join(TITLE_IX + SEX_BASED + SEXUAL_MISCONDUCT), re.I)], 2),
            "harassment_hate": Rule("harassment_hate", "conduct",
                                    [re.compile("|".join(CONDUCT + BIAS_HOSTILITY + THREAT_OR_ATTACK + HATE_BIAS),
                                                re.I)], 3),
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
