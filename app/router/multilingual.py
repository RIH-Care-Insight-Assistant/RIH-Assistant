"""Explicit crisis wording in languages other than English (red-team finding SB-07).

Escalate-only: a match can raise a message to `urgent_safety`; it never lowers or replaces
a lane. Only explicit expressions of wanting to die, suicide, killing or hurting oneself
are listed, not distress in general. Idioms that use "die" for hunger, boredom or laughter
are left out on purpose ("me muero de hambre", "je meurs de faim", "想死你了").

STATUS: drafted by the coding agent on 2026-10-15. Not reviewed by a native speaker or a
clinician. Routing patterns change only through PRs Devika reviews (docs/safety/
crisis-routing.md); every entry here needs that review, and native-speaker review before
any real use. Languages not listed fall through to the keyword router, which only reads
English; the API then adds an unsupported-language notice (app/router/language.py).

Two views of the text are matched:
- "folded": NFKC, format characters removed, casefolded, apostrophes unified, accents
  removed ("daño" -> "dano", "não" -> "nao"). Used for Latin-script languages.
- "plain": NFKC, format characters removed, casefolded, Arabic letter variants and
  diacritics unified, Devanagari nukta removed, "ё" -> "е". Used for other scripts and
  for Vietnamese, whose tone marks carry meaning.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Optional, Tuple

STATUS = "agent-drafted 2026-10-15; awaiting Devika's routing review and native-speaker/clinical review"

_APOSTROPHES = re.compile("[\u2018\u2019\u201a\u201b\u02b9\u02bb\u02bc\u2032\u00b4`\uff07]")
_ARABIC_ALEF = re.compile("[\u0622\u0623\u0625\u0671]")
_ARABIC_MARKS = re.compile("[\u064b-\u065f\u0670\u0640]")

# lang -> (name, [(view, pattern), ...])
LEXICON: Dict[str, Tuple[str, List[Tuple[str, str]]]] = {
    "es": ("Spanish", [
        ("folded", r"\b(quiero|quisiera|deseo|queria|ganas\s+de)\s+(morir(me)?|matarme|suicidarme|"
                   r"quitarme\s+la\s+vida|hacerme\s+dano|lastimarme)\b"),
        ("folded", r"\b(voy\s+a|pienso\s+en|pensando\s+en|intente|intento)\s+(matarme|suicidarme|"
                   r"quitarme\s+la\s+vida|hacerme\s+dano|lastimarme)\b"),
        ("folded", r"\bme\s+(quiero|quisiera)\s+(morir|matar|suicidar)\b"),
        ("folded", r"\bme\s+voy\s+a\s+(matar|suicidar)\b"),
        ("folded", r"\b(suicidarme|suicidarse|suicidarte|suicidio|suicida|suicidas)\b"),
        ("folded", r"\bno\s+quiero\s+(seguir\s+)?vivir\b"),
        ("folded", r"\b(acabar\s+con\s+mi\s+vida|cortarme\s+las\s+venas)\b"),
        ("folded", r"\b(estaria|estarian|estarias)\s+mejor\s+(sin\s+mi|muert[oa]s?)\b"),
        ("folded", r"\b(ojala|quisiera|desearia)\s+(estar|estuviera)\s+muert[oa]\b"),
        ("folded", r"\bse\s+(quiere|quiso|va\s+a)\s+(suicidar|matar)\b"),
    ]),
    "fr": ("French", [
        ("folded", r"\b(je\s+veux|j'?ai\s+envie\s+de|je\s+voudrais|envie\s+de)\s+(mourir|me\s+tuer|"
                   r"me\s+suicider|en\s+finir)\b"),
        ("folded", r"\b(me|se|te)\s+suicider\b"),
        ("folded", r"\bsuicidaires?\b"),
        ("folded", r"\bje\s+(ne\s+)?veux\s+plus\s+vivre\b"),
        ("folded", r"\bmettre\s+fin\s+a\s+((mes|ses|tes)\s+jours|ma\s+vie)\b"),
        ("folded", r"\bje\s+vais\s+me\s+(tuer|suicider)\b"),
        ("folded", r"\bje\s+(veux|vais)\s+me\s+faire\s+du\s+mal\b"),
    ]),
    "pt": ("Portuguese", [
        ("folded", r"\b(quero|queria)\s+(morrer|me\s+matar|me\s+suicidar|tirar\s+(a\s+)?minha\s+(propria\s+)?vida)\b"),
        ("folded", r"\bvou\s+(me\s+matar|me\s+suicidar|tirar\s+(a\s+)?minha\s+(propria\s+)?vida)\b"),
        ("folded", r"\bnao\s+quero\s+(mais\s+viver|viver\s+mais)\b"),
        ("folded", r"\b(se|me)\s+suicidar\b"),
        ("folded", r"\b(quero|vou)\s+me\s+(machucar|cortar)\b"),
    ]),
    "de": ("German", [
        ("folded", r"\bich\s+(will|mochte|wurde\s+gerne?)\s+(sterben|tot\s+sein)\b"),
        ("folded", r"\bmich\s+(umbringen|umzubringen|toten|selbst\s+toten)\b"),
        ("folded", r"\b(selbstmord|suizid)\w*"),
        ("folded", r"\bich\s+(will|mochte)\s+nicht\s+mehr\s+leben\b"),
        ("folded", r"\b(will|werde|mochte)\s+mich\s+(selbst\s+)?verletzen\b"),
    ]),
    "it": ("Italian", [
        ("folded", r"\b(voglio|vorrei)\s+(morire|uccidermi|suicidarmi|farla\s+finita|togliermi\s+la\s+vita)\b"),
        ("folded", r"\b(penso\s+di|pensando\s+di|sto\s+per|ho\s+voglia\s+di)\s+(uccidermi|suicidarmi|"
                   r"togliermi\s+la\s+vita|farla\s+finita)\b"),
        ("folded", r"\bsuicidarmi\b"),
        ("folded", r"\bnon\s+voglio\s+piu\s+vivere\b"),
    ]),
    "zh": ("Chinese", [
        ("plain", r"自杀|自殺|轻生|輕生|不想活|活不下去|割腕|结束(自己的)?生命|結束(自己的)?生命"),
        ("plain", r"想死(?![你您他她它])"),  # "想死你了" means "I miss you so much"
    ]),
    "ja": ("Japanese", [
        ("plain", r"死にたい|生きていたくない|自殺"),
    ]),
    "ko": ("Korean", [
        ("plain", r"자살|죽고\s*싶|살고\s*싶지\s*않|자해|극단적\s*선택"),
    ]),
    "vi": ("Vietnamese", [
        ("plain", r"muốn\s+chết|tự\s+tử|tự\s+sát|không\s+muốn\s+sống"),
        ("folded", r"\b(muon\s+chet|khong\s+muon\s+song)\b"),  # typed without tone marks
    ]),
    "hi": ("Hindi", [
        ("plain", r"आत्महत्या|खुदकुशी|मरना\s*चाहत|जान\s*देना\s*चाहत|खुद\s*को\s*मार"),
        ("folded", r"\b(marna|mar\s+jana)\s+(chahta|chahti|chahte|hai)\b"),  # romanized Hindi
        ("folded", r"\b(aatmahatya|atmahatya|aatmhatya|atmhatya|khudkushi|khudkhushi)\b"),
        ("folded", r"\bkhud\s+ko\s+maa?r\s*(na|dunga|dungi|lunga|lungi|dalunga|dalungi)\b"),
    ]),
    "ar": ("Arabic", [
        ("plain", r"انتحار|انتحر|اريد\s+ان\s+اموت|اريد\s+الموت|اقتل\s+نفسي|انهي\s+حياتي|انهاء\s+حياتي"),
    ]),
    "ru": ("Russian", [
        ("plain", r"хочу\s+умереть|покончить\s+с\s+собой|покончу\s+с\s+собой|суицид|самоубийств|"
                  r"убить\s+себя|убью\s+себя|не\s+хочу\s+жить"),
    ]),
}

_COMPILED: List[Tuple[str, str, "re.Pattern[str]"]] = [
    (lang, view, re.compile(rx, re.IGNORECASE))
    for lang, (_name, entries) in LEXICON.items()
    for view, rx in entries
]


def _base(text: str) -> str:
    t = unicodedata.normalize("NFKC", text or "")
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Cf")
    return t.casefold()


def plain_view(text: str) -> str:
    t = _base(text)
    t = _ARABIC_ALEF.sub("\u0627", t).replace("\u0649", "\u064a")
    t = _ARABIC_MARKS.sub("", t)
    t = t.replace("\u093c", "").replace("\u0451", "\u0435")
    return re.sub(r"\s+", " ", t).strip()


def folded_view(text: str) -> str:
    t = _APOSTROPHES.sub("'", _base(text))
    t = "".join(ch for ch in unicodedata.normalize("NFD", t) if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", t).strip()


def crisis_language(text: str) -> Optional[str]:
    """Language code of the first lexicon entry that matches `text`, or None."""
    if not text:
        return None
    views = {"plain": plain_view(text), "folded": folded_view(text)}
    for lang, view, pat in _COMPILED:
        if pat.search(views[view]):
            return lang
    return None
