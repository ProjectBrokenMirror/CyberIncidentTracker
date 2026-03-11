from app.pipeline.dedup import deduplicate


def test_deduplicate_removes_duplicate_title_source_pairs() -> None:
    records = [
        {"source_name": "databreaches_net", "title": "ACME incident"},
        {"source_name": "databreaches_net", "title": "ACME incident"},
        {"source_name": "hhs_ocr", "title": "ACME incident"},
    ]
    assert len(deduplicate(records)) == 2
