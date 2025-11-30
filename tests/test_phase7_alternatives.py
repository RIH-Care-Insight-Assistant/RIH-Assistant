from app.agent.dispatcher import Dispatcher

def _make_dispatcher():
    return Dispatcher(force_mode="RULE")

def test_decline_counseling_gets_alternatives():
    d = _make_dispatcher()
    out = d.respond("I don't want counseling at RIH, are there any other options?")
    text = out["text"]

    assert "Retriever Activity Center (RAC)" in text
    assert "Wellness initiatives" in text
    assert "myUMBC" in text
    assert any(ev["event"] == "alternatives" for ev in out["trace"])


def test_no_decline_no_alternatives():
    d = _make_dispatcher()
    out = d.respond("Where is RIH located?")
    text = out["text"]

    assert "Retriever Activity Center (RAC)" not in text
