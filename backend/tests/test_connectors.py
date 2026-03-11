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


def test_sec_8k_atom_feed_parses_form_prefix_format(monkeypatch) -> None:
    atom_payload = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>8-K - GLOBEX CORP - Current report filing</title>
    <updated>2026-03-11T17:45:00-04:00</updated>
    <link href="https://www.sec.gov/ixviewer/ix.html?doc=/Archives/example2.htm" />
  </entry>
</feed>
"""

    def fake_get(*args, **kwargs):
        return SimpleNamespace(text=atom_payload, raise_for_status=lambda: None)

    monkeypatch.setattr("app.connectors.sec_8k.httpx.get", fake_get)
    records = Sec8KConnector().fetch()
    assert len(records) == 1
    assert records[0].organization_name == "GLOBEX CORP"


def test_hhs_ocr_parses_entries(monkeypatch) -> None:
    frontpage = """
<html><body>
  <input type="hidden" name="javax.faces.ViewState" value="abc123" />
</body></html>
"""
    report_page = """
<html><body>
  <table>
    <tbody id="ocrForm:reportResultTable_data">
      <tr>
        <td></td>
        <td><span>Sample Health System</span></td>
        <td>TX</td>
        <td>Healthcare Provider</td>
        <td>1234</td>
        <td>03/11/2026</td>
        <td><span>Hacking/IT Incident</span></td>
        <td><span>Network Server</span></td>
      </tr>
    </tbody>
  </table>
</body></html>
"""

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, *args, **kwargs):
            return SimpleNamespace(text=frontpage, raise_for_status=lambda: None)

        def post(self, *args, **kwargs):
            return SimpleNamespace(text=report_page, raise_for_status=lambda: None)

    monkeypatch.setattr("app.connectors.hhs_ocr.httpx.Client", lambda **kwargs: FakeClient())
    connector = HhsOcrConnector()
    records = connector.fetch()

    assert len(records) == 1
    assert records[0].source_name == "hhs_ocr"
    assert records[0].organization_name == "Sample Health System"
