"""Implicit suicide-risk warning signs without explicit trigger words (red-team finding SB-08).

Escalate-only, like the multilingual lexicon: a match can raise a message to
`urgent_safety`, never lower a lane. Two kinds of signal, both deliberately narrow:

- STRONG phrases count on their own: wanting to sleep and never wake up, "won't be a
  burden much longer", "nobody will miss me when I'm gone", a note "to find after I'm
  gone", "decided tonight is my last night", "my last message to anyone", final goodbyes,
  stockpiling pills, wanting to disappear forever, means plus a chosen place or time.
- WEAK signals are ordinary on their own and are routed only when two different kinds
  appear in one message: giving possessions away, goodbye letters or goodbyes to everyone,
  a will, affairs in order, "made a plan", "no way out", buying a rope or gun, "I'm ready
  to go". "I gave away all my things and wrote goodbye letters" has two kinds; "I said
  goodbye to my family at the airport" has one and is not routed.

This cannot recognise implicit risk in general: wording outside these lists is still
missed, and a benign message with two weak signals is routed to crisis (the crisis
template is conditional, as for the caution-biased idioms in docs/safety/crisis-routing.md).

STATUS: drafted by the coding agent on 2026-10-15, informed by commonly published
warning-sign lists, not by a clinician. Routing patterns change only through PRs Devika
reviews; this list needs that review and clinical review before real use.

B10 additions (2026-10-15, Devika's held-out check; docs/audits/devika-final-review-2026-10-15.md):
entries marked "B10" add standard warning-sign wording the held-out set showed missing:
"better off without me", no reason to keep living, not expecting to be alive, never
wanting to wake up again, lethality questions, wanting everything to end for good,
arranging care for after "I'm gone", saving up pills; and two weak kinds ("won't need
them anymore", "made my decision"). Drafted by the coding agent at Devika's direction;
they need the same clinical review as the rest.
"""

from __future__ import annotations

import re
from typing import List, Set

STATUS = ("agent-drafted 2026-10-15 (B10 additions at Devika's direction); awaiting Devika's routing "
          "sign-off and clinical review")

_PILLS = (r"(pills?|tablets?|capsules?|meds|medications?|medicines?|painkillers?|sleeping\s+pills|"
          r"tylenol|advil|ibuprofen|acetaminophen|paracetamol|aspirin|benadryl|xanax|insulin)\b")
_GONE = r"(after|when|once)\s+i'?m\s+(gone|dead)\b(?!\s+(for|to|on|during|over|this|next|until|till|back|from)\b)"

STRONG: List[str] = [
    r"\b(go\s+to\s+sleep|fall\s+asleep|sleep)\s+and\s+(just\s+)?never\s+wake\s+up\b",
    r"\bnever\s+wake\s+up\s+again\b",
    r"\b(won'?t|wont|will\s+not)\s+be\s+(a\s+)?(burden|problem|bother|nuisance)\s+"
    r"(to\s+(anyone|anybody|everyone|everybody|you|you\s+all|my\s+\w+)\s+)?"
    r"(much\s+longer|for\s+(much\s+)?longer|anymore|any\s+more|for\s+long|soon)\b",
    r"\b(won'?t|wont|will\s+not)\s+be\s+(around|here|alive)\s+(much\s+longer|for\s+(much\s+)?long(er)?\b|"
    r"to\s+(bother|annoy|burden|worry|bug|trouble)\b)",
    r"\b((nobody|no\s+one|no-one|noone)\s+(will|would)|(they|you|anyone|people|my\s+\w+)\s+(won'?t|wouldn'?t|will\s+not))"
    r"\s+(even\s+)?(miss|notice|care)\b[^.!?]{0,20}?\b" + _GONE,
    r"\b(notes?|letters?|messages?)\b[^.!?]{0,40}?\bto\s+(find|read)\b[^.!?]{0,20}?\b" + _GONE,
    r"\b(decided|deciding|know)\s+(that\s+)?(tonight|today|this\s+(week|weekend))\s+(is|will\s+be)\s+(my|the)\s+last\b"
    r"(?!\s+(day|night|time|shift|class)\s+(of|at|in|before|for|on)\b)",
    r"\blast\s+(night|day)\s+(alive|on\s+earth|in\s+this\s+world)\b",
    r"\b(this|it)\s+(is|will\s+be|'s)\s+my\s+(last|final)\s+(message|post|text|note|words?)\s+"
    r"(to\s+(anyone|anybody|everyone|everybody|you\s+all|the\s+world)|ever)\b",
    r"\b(saying|say|said|writing|wrote|written|sending|sent|making)\s+my\s+(final|last)\s+goodbyes?"
    r"(\s+to\s+(everyone|everybody|the\s+world|you\s+all|all\s+of\s+you|my\s+(family|friends|loved\s+ones)))?"
    r"\s*([.!?,;]|$)",
    r"\b(stockpil|hoard)(e|es|ed|ing)\s+(up\s+)?(on\s+)?((all\s+)?my|the|some)?\s*" + _PILLS,
    r"\b(want|wanna|wish\s+i\s+could|going\s+to|gonna)\s+(to\s+)?disappear\s+(forever|for\s+good|permanently)\b",
    r"\b(bought|got|have|found|buying|getting|ordered)\s+(a\s+|the\s+|some\s+)?(rope|noose|gun|pistol|firearm|"
    r"razor\s+blades?)\b[^.!?]{0,40}?\b(know|picked|chose|planned|decided)\s+(where|when|how)\b",
    r"\b(i'?m|i\s+am)\s+ready\s+to\s+die\b",
    # B10 additions
    r"\b(everyone|everybody|they|you|people|my\s+\w+|the\s+world|all\s+of\s+you|you\s+all)\s+(would|will|'?d)\s+"
    r"(all\s+)?be\s+better\s+off\s+(without\s+me|if\s+i\s+(was|were)\s+(dead|gone|never\s+born))\b"
    r"(?!\s+(on|in|at|for)\s+(the|this|my|our|a)\s+(team|project|group|lab|shift|trip|class)\b)",
    r"\b(no|any|don'?t\s+have\s+a(ny)?)\s+(reason|point)\s+(for\s+me\s+)?(in\s+|to\s+)?(keep\s+|go\s+on\s+|going\s+on\s+)?"
    r"(living|being\s+alive|staying\s+alive|to\s+live(?!\s+(on|in|off|at|with|near|here|there|together|abroad)\b))",
    r"\b(won'?t|wont|will\s+not|don'?t\s+think\s+i'?ll|not\s+going\s+to)\s+(still\s+)?be\s+alive\b",
    r"\b(never|don'?t|do\s+not)\s+want\s+to\s+wake\s+up\s+(again|ever|anymore|any\s+more)\b",
    r"\bnever\s+want\s+to\s+wake\s+up\s*([.!?,;]|$)",
    r"\bhow\s+(many|much)\b[^.!?]{0,60}?\b(would|does|will|should|do)\s+(it|i|you)\s+(take|need)\s+to\s+"
    r"(die|not\s+wake\s+up|never\s+wake\s+up|kill\s+(me|myself)|overdose|od)\b",
    r"\b(want|wish|need)\s+(it\s+all|everything|all\s+of\s+(it|this))\s+to\s+(end|stop|be\s+over)\s+"
    r"(permanently|forever|for\s+good)\b",
    r"\bwant\s+it\s+all\s+to\s+end\b(?!\s+(soon|already|so|and\s+then)\b)",
    r"\b(take\s+care\s+of|look\s+after|feed|adopt|walk)\b[^.!?]{0,40}?\b" + _GONE,
    r"\blast\s+(message|text|post|note)\s+(i'?ll|i\s+will)\s+ever\s+(send|write|post)\b",
    r"\b((saving|saved)\s+up|stash(ing|ed)?(\s+up)?)\s+(on\s+)?((all\s+)?my|the|some)?\s*(\w+\s+)?" + _PILLS,
]

WEAK = {
    "possessions": r"\b((gave|give|giving|given)\s+away|(got|get|getting|gotten)\s+rid\s+of)\s+"
                   r"((all|most)\s+(of\s+)?)?my\s+(things|stuff|belongings|possessions|clothes|books|pets?|cat|dog|"
                   r"games|money|savings|valuables|jewelry|guitar)\b",
    "goodbye": r"\b(goodbye|good-bye|farewell)\s+(letters?|notes?|messages?|texts?|videos?|emails?)\b"
               r"|\b(saying|say|said|telling)\s+(my\s+)?goodbyes?\s+to\s+(everyone|everybody|all\s+my\s+(friends|family)|"
               r"my\s+(family|friends|parents|loved\s+ones))\b",
    "will": r"\b(wrote|written|writing|made|updated|finished)\s+(my|a)\s+will\b",
    "affairs": r"\b(put|putting|get|getting|got|have)\s+(all\s+)?my\s+affairs\s+in\s+order\b",
    "plan": r"\b(made|have|got|making|came\s+up\s+with)\s+a\s+plan\b(?!\s+(to|for|with|of|about|b)\b)",
    "no_way_out": r"\b(no|(don'?t|can'?t)\s+see\s+(a|any)|there'?s\s+no)\s+way\s+out\b"
                  r"(?!\s+of\s+(the|this|my|a)\s+(lease|contract|class|course|parking|building|room|maze|exam|test|"
                  r"meeting)\b)",
    "means": r"\b(bought|got|have|found|buying|getting|ordered)\s+(a\s+|the\s+|some\s+)?(rope|gun|pistol|firearm)\b",
    "ready": r"\b(i'?m|i\s+am)\s+ready\s+to\s+go\b(?!\s+(to|home|out|back|now|on|for|with|and|shopping|there)\b)",
    # B10 additions
    "no_need": r"\b(won'?t|wont|will\s+not)\s+(need|be\s+needing)\s+(it|them|this|these|those|anything|any\s+of\s+(it|this|them))"
               r"\s+(anymore|any\s+more|where\s+i'?m\s+going|after\s+(tonight|today|this\s+week))\b",
    "decided": r"\b(made|i'?ve\s+made)\s+(my|the)\s+(decision|choice)\b(?!\s+(about|on|to|regarding|for|between|of)\b)"
               r"(?![^.!?]{0,20}\b(major|class|course|school|college|offer|job|apartment|roommate)\b)",
}

_STRONG_RE = [re.compile(rx, re.IGNORECASE) for rx in STRONG]
_WEAK_RE = {kind: re.compile(rx, re.IGNORECASE) for kind, rx in WEAK.items()}


def weak_kinds(views: List[str]) -> Set[str]:
    return {kind for kind, pat in _WEAK_RE.items() if any(pat.search(v) for v in views)}


def implicit_risk(views: List[str]) -> bool:
    """True if any view has a strong warning sign, or the views together have two kinds of weak sign."""
    if any(p.search(v) for p in _STRONG_RE for v in views):
        return True
    return len(weak_kinds(views)) >= 2
