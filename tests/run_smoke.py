from app.agent.dispatcher import Dispatcher


def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)


def test_routes():
    d = Dispatcher()

    crisis = d.respond("i want to kms")
    _assert("988" in crisis["text"], "Crisis template should be returned for kms")

    tix = d.respond("I was harassed by someone")
    _assert("Title IX" in tix["text"], "Title IX template should appear for 'harassed'")

    ret = d.respond("I want to drop from college")
    _assert("Advising" in ret["text"] or "advis" in ret["text"].lower(), "Retention template should appear")

    appt = d.respond("how do I book an appointment")
    _assert("Here’s what I found" in appt["text"], "Appointments should go to KB retrieval")


def test_misspelling_and_negative():
    d = Dispatcher()

    # Misspelling normalization ("harrased" -> "harassed")
    tix_misspell = d.respond("I was harrased yesterday")
    _assert("Title IX" in tix_misspell["text"], "Misspelling should still route to Title IX")

    # Crisis euphemism ("unalive")
    crisis_euphemism = d.respond("I feel like I want to unalive myself")
    _assert("988" in crisis_euphemism["text"], "Euphemism should route to crisis")

    # Benign query should NOT trigger safety templates
    benign = d.respond("I love campus food")
    _assert(("Title IX" not in benign["text"]) and ("988" not in benign["text"]),
            "Benign query should not trigger safety templates")


def main():
    test_routes()
    test_misspelling_and_negative()
    print("Smoke OK")


if __name__ == "__main__":
    main()



