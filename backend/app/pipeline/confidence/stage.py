def score_confidence(record: dict) -> dict:
    source = record.get("source_name", "")
    source_weights = {
        "sec_edgar_8k": 0.95,
        "hhs_ocr": 0.92,
        "courtlistener": 0.9,
        "databreaches_net": 0.75,
        "bleeping_computer": 0.72,
    }
    record["confidence"] = source_weights.get(source, 0.6)
    return record
