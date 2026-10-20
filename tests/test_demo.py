import sqlite3

from demo import run_demo


def test_offline_demo_uses_real_pipeline_and_recovers_state(tmp_path, monkeypatch):
    def forbid_network(*args, **kwargs):
        raise AssertionError("The offline example must not contact external services")

    monkeypatch.setattr("scrapers.base_scraper.urlopen", forbid_network)
    monkeypatch.setattr("requests.Session.request", forbid_network)
    first = run_demo(tmp_path)
    assert first["review_count"] == first["recovered_review_count"] == 4
    assert first["calculated_tomatometer"] == 75.0
    assert first["new_reviews_after_restart"] == 0
    assert first["order_intent_count"] > 0
    second = run_demo(tmp_path)
    assert first == second
    with sqlite3.connect(tmp_path / "trade_ledger.sqlite3") as database:
        assert database.execute("SELECT COUNT(*) FROM order_intents").fetchone()[0] == first["order_intent_count"]
