"""Does a message look like it is not in English? (compensating control for SB-07)

The keyword router reads English only, and the multilingual lexicon covers explicit crisis
wording in a few languages. For everything else the assistant should at least say it did
not understand and repeat the emergency numbers, instead of answering silently in English.

This is NOT a safety decision and never changes a lane. A positive adds the
`language_support` notice to ordinary (non-safety) responses. The heuristic is simple on
purpose and errs towards showing the notice:
- mostly non-Latin letters (Chinese, Arabic, Cyrillic, Devanagari, Hangul, ...); or
- at least two words, none of them a common English or campus word, and some positive
  sign of another language (a common non-English function word, or accented letters); or
- at least two common non-English function words outweighing the English ones.
Short messages (one word) never get the notice, and neither do English noun phrases with
no function words ("dining hall menu"). Languages written in plain ASCII whose function
words are not listed are missed (B10 added several; see FOREIGN). A false positive only
adds one notice.
"""

from __future__ import annotations

import re
import unicodedata

from .multilingual import folded_view

NOTICE_KIND = "language_support"
# The Spanish sentence is an agent translation, awaiting native-speaker review.
NOTICE_TEXT = (
    "I can only read English right now, so I may have misunderstood your message. "
    "If you or someone else may be in danger, call or text 988, or call 911. "
    "(Solo puedo leer inglés por ahora. Si tú u otra persona está en peligro, "
    "llama o envía un mensaje de texto al 988, o llama al 911.)"
)

ENGLISH = frozenset("""
a about after again all also always am an and any anyone anything are around as ask asked at away back bad be
because been before being best better between book booking both but by call can can't cannot cant care class classes
close closed college come could day days did didn't didnt do does doesn't doesnt doing don't done dont down during
each email even every everyone everything far feel feeling felt find first for free friend friends from get gets
getting give go goes going gone good got had has have having he hello help her here hey hi him his home how i i'd
i'll i'm i've if im in into is isn't isnt it it's its ive just know last later leave left less let let's like long
look lot made make many may me mine more morning most much must my myself near need needed needs never new next night
no not nothing now of off often ok okay on once one only open opens or other others our out over own people please
really right said same say school see seen she should since so some someone something sometimes soon still such sure
take takes taking talk tell than thank thanks that that's the their them then there these they thing things think
this those through thx time times to today told tomorrow too took two under until up us use very visit wait want
wanted wants was way we week weekend well went were what what's when where which while who why will with without
won't wont work would yeah year yes yet you your yours
after-hours address allergy allergies anxiety appointment appointments bill billing bills booster campus center
clinic cost costs counseling counselor covid depression doctor doctors dorm emergency exam exams fee fees fever flu
form forms grade health hiv hours hour immunization immunizations information info insurance location located
medical medication medications medicine meds mental nurse nurses office online pain pap pay payment pharmacy phone
pills portal pregnancy prescription prescriptions price professor record records refill requirement requirements
reschedule retriever rih roommate schedule scheduling semester service services shot shots sick smear std sti
stress student students study test testing tests therapist therapy tb umbc urgent vaccine vaccines vaccination
vaccinations walk-in monday tuesday wednesday thursday friday saturday sunday
""".split())

FOREIGN = frozenset("""
que de el los las una unos unas por para pero porque como cuando donde estoy esta estas este esto tengo tiene quiero
puedo necesito muy mas tambien hay del yo mi mis su sus es ser fue hola gracias ayuda cita nada todo aqui
je tu il elle nous vous ils elles le les des du et est sont pas mon mes suis veux avec pour dans mais qui
quoi bonjour merci oui tres aussi
eu voce nao meu minha estou quero preciso tenho obrigado obrigada ola muito uma
ich du er sie wir ihr nicht und das der ist mein meine habe haben fur auf ein eine einen kein sehr danke
bitte hallo ja nein vor dieser diese
io sono che mio mia voglio della delle dal nel sei ciao grazie molto anche
ako ko ka siya kami tayo sila ang ng mga sa na nang hindi gusto po salamat
bir ve bu icin degil istiyorum var yok cok merhaba
nie jest sie chce mam jestem dla czy dziekuje tak
nataka sana mimi wewe kwa ni hapana ndiyo asante habari
toi khong cua muon nhung
ce une au il gli di posso perche questo questa hai
aku saya ingin mau tidak yang itu ini dengan untuk dari sudah belum bisa kamu anda kita mereka tolong
ik wil het een niet mijn naar voor zijn geen graag waar wat
vull vols tinc amb aixo perque meva meu estic
mwen vle ou li ki pou kijan kote
vreau nu este sunt pentru
hoon hai nahi mujhe kya kaise mera meri aap kyun
""".split())
# B10 (Devika's held-out check): the last seven lines add frequent function words of Italian,
# French, Indonesian/Malay, Dutch, Catalan, Haitian Creole, Romanian and romanized Hindi, so
# that plain-ASCII messages in those languages get the notice. Words that are also common in
# English ("van", "un", "non", "dove", "son", "pa", "dan") are deliberately left out.

# Words that are common in English and in other languages ("me", "no", "in", German
# "will"); they count as neither English nor foreign.
AMBIGUOUS = frozenset("a an as die do in me no will".split())

_WORD = re.compile(r"[a-z]+(?:['-][a-z]+)?")


def unsupported_language(text: str) -> bool:
    t = unicodedata.normalize("NFKC", text or "")
    letters = [c for c in t if c.isalpha()]
    if not letters:
        return False
    latin = sum(1 for c in letters if unicodedata.name(c, "").startswith("LATIN"))
    if (len(letters) - latin) / len(letters) >= 0.5:
        return True
    tokens = _WORD.findall(folded_view(t))
    if len(tokens) < 2:
        return False
    english = sum(1 for w in tokens if w in ENGLISH and w not in AMBIGUOUS)
    foreign = sum(1 for w in tokens if w in FOREIGN)
    accented = any(ord(c) > 127 for c in letters)
    if english == 0 and (foreign >= 1 or accented):
        return True
    return foreign >= 2 and foreign > english
