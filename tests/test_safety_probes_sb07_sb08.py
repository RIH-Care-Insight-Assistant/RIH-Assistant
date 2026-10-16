"""The pre-registered SB-07/SB-08 probe set (committed before the mitigation) as a regression.

Uncovered languages are a measured gap: their messages are expected to get the language
notice, not the crisis template. This test does not claim they are routed.
"""

from scripts.safety_probes import evaluate


def test_probe_groups_meet_their_expectations():
    report = evaluate()
    g = report["groups"]
    for name in ("multilingual_crisis", "multilingual_benign", "implicit_risk", "implicit_benign", "english_ordinary"):
        assert g[name]["lane_ok"] == g[name]["n"], name
        assert g[name]["cli_ok"] == g[name]["n"], name
        assert g[name]["api_ok"] == g[name]["n"], name
    for name in ("multilingual_crisis_uncovered", "multilingual_benign", "english_ordinary"):
        assert g[name]["notice_ok"] == g[name]["notice_n"], name


def test_uncovered_languages_are_still_a_gap():
    rows = [r for r in evaluate()["cases"] if r["group"] == "multilingual_crisis_uncovered"]
    assert rows and all(r["language_notice"] for r in rows)
    # Recorded honestly: these are not routed to crisis. If a future change routes them,
    # update the probe documentation rather than this assertion's meaning.
    assert all(r["api_safety_lane"] is None for r in rows)
