from types import SimpleNamespace

from app.connectors.databreach_net import DataBreachesConnector
from app.connectors.hhs_ocr import HhsOcrConnector
from app.connectors.sec_8k import Sec8KConnector


def test_databreaches_challenge_page_returns_no_records(monkeypatch) -> None:
    def fake_get(*args, **kwargs):
        return SimpleNamespace(
            text="<html><title>Just a moment...</title><script>window._cf_chl_opt={}</script></html>",
            raise_for_status=lambda: None,
        )

    monkeypatch.setattr("app.connectors.databreach_net.httpx.get", fake_get)
    connector = DataBreachesConnector()
    assert connector.fetch() == []


def test_sec_8k_atom_feed_parses_entries(monkeypatch) -> None:
    atom_payload = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>ACME CORP - 8-K - Current report filing</title>
    <updated>2026-03-11T17:45:00-04:00</updated>
    <link href="https://www.sec.gov/ixviewer/ix.html?doc=/Archives/example.htm" />
  </entry>
</feed>
"""

    def fake_get(*args, **kwargs):
        return SimpleNamespace(text=atom_payload, raise_for_status=lambda: None)

    monkeypatch.setattr("app.connectors.sec_8k.httpx.get", fake_get)
    connector = Sec8KConnector()
    records = connector.fetch()

    assert len(records) == 1
    assert records[0].source_name == "sec_edgar_8k"
    assert records[0].organization_name == "ACME CORP"


def test_hhs_ocr_json_parses_entries(monkeypatch) -> None:
    payload = [
        {
            "name_of_covered_entity": "Sample Health System",
            "type_of_breach": "Hacking/IT Incident",
            "breach_submission_date": "2026-03-11T12:00:00.000",
        }
    ]

    def fake_get(*args, **kwargs):
        return SimpleNamespace(json=lambda: payload, raise_for_status=lambda: None)

    monkeypatch.setattr("app.connectors.hhs_ocr.httpx.get", fake_get)
    connector = HhsOcrConnector()
    records = connector.fetch()

    assert len(records) == 1
    assert records[0].source_name == "hhs_ocr"
    assert records[0].organization_name == "Sample Health System"
