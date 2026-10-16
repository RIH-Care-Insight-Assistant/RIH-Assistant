"""SB-07: explicit crisis wording in other languages reaches the crisis template.

Escalate-only: the lexicon can raise a message to urgent_safety and never lowers a lane.
Agent-drafted terms, awaiting Devika's routing review and native-speaker review.
"""

import pytest

from app.agent.dispatcher import Dispatcher
from app.agent.orchestrator import Orchestrator
from app.answer.compose import crisis_message
from app.router import multilingual
from app.router.safety_router import crisis_extension, route

POSITIVE = [
    ("es", "quiero morir, ya no aguanto"),
    ("es", "me quiero matar"),
    ("es", "Estoy pensando en SUICIDARME"),
    ("es", "ya no quiero vivir"),
    ("es", "mis padres estarían mejor sin mí"),
    ("es", "ojalá estuviera muerta"),
    ("es", "quiero cortarme las venas"),
    ("es", "mi amiga dice que se quiere suicidar"),
    ("fr", "j’ai envie de mourir"),  # curly apostrophe
    ("fr", "je vais me suicider ce soir"),
    ("fr", "je pense à mettre fin à mes jours"),
    ("pt", "não quero mais viver"),
    ("pt", "quero me matar"),
    ("de", "ich möchte sterben"),
    ("de", "ich habe Selbstmordgedanken"),
    ("it", "vorrei togliermi la vita"),
    ("it", "non voglio più vivere"),
    ("zh", "我真的想死"),
    ("zh", "我活不下去了"),
    ("ja", "もう死にたい"),
    ("ko", "죽고 싶다"),
    ("vi", "toi muon chet"),  # typed without tone marks
    ("vi", "tôi không muốn sống nữa"),
    ("hi", "मुझे आत्महत्या के विचार आते हैं"),
    ("hi", "mujhe marna hai"),
    ("ar", "اريد ان اموت"),  # without hamza
    ("ru", "я думаю о суициде"),
]

BENIGN = [
    "me muero de hambre",
    "me muero de risa",
    "me voy a morir de vergüenza si repruebo",
    "quiero aprender a cortarme el pelo",
    "¿dónde puedo vacunarme contra la gripe?",
    "je meurs de faim",
    "j'ai envie de manger",
    "estou morrendo de fome",
    "vou morrer de vergonha",
    "ich sterbe vor Langeweile",
    "muoio dal ridere",
    "想死你了",
    "笑死我了",
    "我想预约",
    "死ぬほど眠い",
    "배고파 죽겠어",
    "mujhe doctor se milna hai",
    "я умираю от скуки",
]


@pytest.mark.parametrize("lang,text", POSITIVE)
def test_explicit_crisis_wording_routes_to_crisis(lang, text):
    assert multilingual.crisis_language(text) == lang
    assert route(text).level == "urgent_safety"


@pytest.mark.parametrize("text", BENIGN)
def test_idioms_and_ordinary_requests_are_not_crisis(text):
    assert multilingual.crisis_language(text) is None
    r = route(text)
    assert r is None or r.level != "urgent_safety"


def test_every_lexicon_language_has_a_positive_test():
    assert {lang for lang, _ in POSITIVE} == set(multilingual.LEXICON)


def test_lexicon_is_labelled_unreviewed():
    assert "awaiting" in multilingual.STATUS and "review" in multilingual.STATUS


@pytest.mark.parametrize("text", ["quiero morir", "我想死"])
def test_every_public_path_returns_the_exact_crisis_template(text, monkeypatch):
    assert Dispatcher(force_mode="RULE").respond(text)["text"] == crisis_message()
    res = Orchestrator().run(text)
    assert res.is_terminal_safety and res.safety_lane == "urgent_safety" and res.text == crisis_message()
    assert res.notices == []  # the safety template is never extended with a notice
    from app.ui import cli

    monkeypatch.setattr(cli, "log", lambda *a, **k: None)
    for mode in ("LEGACY", "AGENT"):
        monkeypatch.setenv("RIH_MODE", mode)
        assert cli.respond(text) == crisis_message()


def test_crisis_outranks_title_ix_in_one_message():
    text = "I was sexually assaulted and quiero morir"
    assert route("I was sexually assaulted").level == "title_ix"
    assert route(text).level == "urgent_safety"


def test_escalation_never_lowers_an_english_lane():
    for text, lane in [("I want to kill myself, quiero ayuda", "urgent_safety"),
                       ("someone is stalking me, ayuda por favor", "title_ix"),
                       ("I need a counseling appointment, gracias", "counseling")]:
        assert route(text).level == lane


def test_mixed_language_message_is_caught():
    assert route("honestly I just keep thinking me quiero morir").level == "urgent_safety"
    assert crisis_extension("honestly I just keep thinking me quiero morir") == "multilingual:es"


def test_invisible_characters_do_not_hide_a_term():
    assert route("quiero mo\u200brir").level == "urgent_safety"
    assert route("自\u200b杀").level == "urgent_safety"
